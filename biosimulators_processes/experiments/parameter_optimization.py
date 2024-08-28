import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

# Define the biological ODE
def biological_system(t, x, A, B, C):
    # Example dynamics
    dxdt = A * x[0] - B * x[1] * x[0] + C * np.cos(x[0])
    return [dxdt]

# Define the cost function to be minimized
def cost_function(params):
    A, B, C = params
    initial_conditions = [1.0]  # Initial state of the system
    t_span = (0, 10)  # Time span for the simulation
    
    # Solve the ODE
    sol = solve_ivp(biological_system, t_span, initial_conditions, args=(A, B, C))
    
    # Define the output D as the last value of the first state variable
    D = sol.y[0, -1]
    
    return D  # We want to minimize this value

# Initial guess for parameters A, B, C
initial_guess = [0.5, 0.5, 0.5]

# Perform the optimization
result = minimize(cost_function, initial_guess, method='BFGS')

print("Optimal parameters:", result.x)
print("Minimum value of D:", result.fun)