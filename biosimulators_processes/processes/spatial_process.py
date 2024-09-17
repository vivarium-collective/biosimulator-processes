import numpy as np
import dolfinx
import ufl
from mpi4py import MPI
from petsc4py import PETSc
from basix.ufl import element, mixed_element
from dolfinx import default_real_type, fem, la
from dolfinx.fem import (
    Constant,
    Function,
    dirichletbc,
    extract_function_spaces,
    form,
    functionspace,
    locate_dofs_topological,
)
from dolfinx.fem.petsc import assemble_matrix_block, assemble_vector_block
from dolfinx.io import XDMFFile
from dolfinx.mesh import CellType, create_rectangle, locate_entities_boundary
from ufl import div, dx, grad, inner
from process_bigraph import Process

from biosimulators_processes import CORE


class FEMProcess(Process):
    config_schema = {}

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

        # create mesh
        self.msh = create_rectangle(
            MPI.COMM_WORLD, [np.array([0, 0]), np.array([1, 1])], [32, 32], CellType.triangle
        )

        # configure function space
        P2 = element("Lagrange", self.msh.basix_cell(), 2, shape=(self.msh.geometry.dim,), dtype=default_real_type)
        P1 = element("Lagrange", self.msh.basix_cell(), 1, dtype=default_real_type)
        self.V, self.Q = functionspace(self.msh, P2), functionspace(self.msh, P1)

        # No-slip condition on boundaries where x = 0, x = 1, and y = 0
        noslip = np.zeros(msh.geometry.dim, dtype=PETSc.ScalarType)  # type: ignore
        facets = locate_entities_boundary(self.msh, 1, noslip_boundary)
        bc0 = dirichletbc(noslip, locate_dofs_topological(self.V, 1, facets), self.V)

        # Driving (lid) velocity condition on top boundary (y = 1)
        lid_velocity = Function(self.V)
        lid_velocity.interpolate(lid_velocity_expression)
        facets = locate_entities_boundary(self.msh, 1, lid)
        bc1 = dirichletbc(lid_velocity, locate_dofs_topological(self.V, 1, facets))

        # Collect Dirichlet boundary conditions
        self.bcs = [bc0, bc1]

        # Define variational problem
        (u, p) = ufl.TrialFunction(self.V), ufl.TrialFunction(self.Q)
        (v, q) = ufl.TestFunction(self.V), ufl.TestFunction(self.Q)
        f = Constant(msh, (PETSc.ScalarType(0), PETSc.ScalarType(0)))  # type: ignore

        self.a = form([[inner(grad(u), grad(v)) * dx, inner(p, div(v)) * dx], [inner(div(u), q) * dx, None]])
        self.L = form([inner(f, v) * dx, inner(Constant(msh, PETSc.ScalarType(0)), q) * dx])  # type: ignore
        self.a_p11 = form(inner(p, q) * dx)
        self.a_p = [[self.a[0][0], None], [None, self.a_p11]]

    def initial_state(self):
        return {}

    def inputs(self):
        pass

    def outputs(self):
        return {'norm_u': 'float', 'norm_p': 'float'}

    def nested_iterative_solver(self):
        """Solve the Stokes problem using nest matrices and an iterative solver."""

        # Assemble nested matrix operators
        A = fem.petsc.assemble_matrix_nest(self.a, bcs=self.bcs)
        A.assemble()

        # Create a nested matrix P to use as the preconditioner. The
        # top-left block of P is shared with the top-left block of A. The
        # bottom-right diagonal entry is assembled from the form a_p11:
        P11 = fem.petsc.assemble_matrix(self.a_p11, [])
        P = PETSc.Mat().createNest([[A.getNestSubMatrix(0, 0), None], [None, P11]])
        P.assemble()

        A00 = A.getNestSubMatrix(0, 0)
        A00.setOption(PETSc.Mat.Option.SPD, True)

        P00, P11 = P.getNestSubMatrix(0, 0), P.getNestSubMatrix(1, 1)
        P00.setOption(PETSc.Mat.Option.SPD, True)
        P11.setOption(PETSc.Mat.Option.SPD, True)

        # Assemble right-hand side vector
        b = fem.petsc.assemble_vector_nest(self.L)

        # Modify ('lift') the RHS for Dirichlet boundary conditions
        fem.petsc.apply_lifting_nest(b, self.a, bcs=self.bcs)

        # Sum contributions for vector entries that are share across
        # parallel processes
        for b_sub in b.getNestSubVecs():
            b_sub.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)

        # Set Dirichlet boundary condition values in the RHS vector
        bcs0 = fem.bcs_by_block(extract_function_spaces(self.L), self.bcs)
        fem.petsc.set_bc_nest(b, bcs0)

        # The pressure field is determined only up to a constant. We supply
        # a vector that spans the nullspace to the solver, and any component
        # of the solution in this direction will be eliminated during the
        # solution process.
        null_vec = fem.petsc.create_vector_nest(self.L)

        # Set velocity part to zero and the pressure part to a non-zero
        # constant
        null_vecs = null_vec.getNestSubVecs()
        null_vecs[0].set(0.0), null_vecs[1].set(1.0)

        # Normalize the vector that spans the nullspace, create a nullspace
        # object, and attach it to the matrix
        null_vec.normalize()
        nsp = PETSc.NullSpace().create(vectors=[null_vec])
        assert nsp.test(A)
        A.setNullSpace(nsp)

        # Create a MINRES Krylov solver and a block-diagonal preconditioner
        # using PETSc's additive fieldsplit preconditioner
        ksp = PETSc.KSP().create(self.msh.comm)
        ksp.setOperators(A, P)
        ksp.setType("minres")
        ksp.setTolerances(rtol=1e-9)
        ksp.getPC().setType("fieldsplit")
        ksp.getPC().setFieldSplitType(PETSc.PC.CompositeType.ADDITIVE)

        # Define the matrix blocks in the preconditioner with the velocity
        # and pressure matrix index sets
        nested_IS = P.getNestISs()
        ksp.getPC().setFieldSplitIS(("u", nested_IS[0][0]), ("p", nested_IS[0][1]))

        # Set the preconditioners for each block. For the top-left
        # Laplace-type operator we use algebraic multigrid. For the
        # lower-right block we use a Jacobi preconditioner. By default, GAMG
        # will infer the correct near-nullspace from the matrix block size.
        ksp_u, ksp_p = ksp.getPC().getFieldSplitSubKSP()
        ksp_u.setType("preonly")
        ksp_u.getPC().setType("gamg")
        ksp_p.setType("preonly")
        ksp_p.getPC().setType("jacobi")

        # Create finite element {py:class}`Function <dolfinx.fem.Function>`s
        # for the velocity (on the space `V`) and for the pressure (on the
        # space `Q`). The vectors for `u` and `p` are combined to form a
        # nested vector and the system is solved.
        u, p = Function(self.V), Function(self.Q)
        x = PETSc.Vec().createNest([la.create_petsc_vector_wrap(u.x), la.create_petsc_vector_wrap(p.x)])
        ksp.solve(b, x)

        # Save solution to file in XDMF format for visualization, e.g. with
        # ParaView. Before writing to file, ghost values are updated using
        # `scatter_forward`.
        with XDMFFile(MPI.COMM_WORLD, "out_stokes/velocity.xdmf", "w") as ufile_xdmf:
            u.x.scatter_forward()
            P1 = element(
                "Lagrange", self.msh.basix_cell(), 1, shape=(self.msh.geometry.dim,), dtype=default_real_type
            )
            u1 = Function(functionspace(self.msh, P1))
            u1.interpolate(u)
            ufile_xdmf.write_mesh(self.msh)
            ufile_xdmf.write_function(u1)

        with XDMFFile(MPI.COMM_WORLD, "out_stokes/pressure.xdmf", "w") as pfile_xdmf:
            p.x.scatter_forward()
            pfile_xdmf.write_mesh(self.msh)
            pfile_xdmf.write_function(p)

        # Compute norms of the solution vectors
        norm_u = la.norm(u.x)
        norm_p = la.norm(p.x)
        if MPI.COMM_WORLD.rank == 0:
            print(f"(A) Norm of velocity coefficient vector (nested, iterative): {norm_u}")
            print(f"(A) Norm of pressure coefficient vector (nested, iterative): {norm_p}")

        return norm_u, norm_p


# Function to mark x = 0, x = 1 and y = 0
def noslip_boundary(x):
    return np.isclose(x[0], 0.0) | np.isclose(x[0], 1.0) | np.isclose(x[1], 0.0)


# Function to mark the lid (y = 1)
def lid(x):
    return np.isclose(x[1], 1.0)


# Lid velocity
def lid_velocity_expression(x):
    return np.stack((np.ones(x.shape[1]), np.zeros(x.shape[1])))
