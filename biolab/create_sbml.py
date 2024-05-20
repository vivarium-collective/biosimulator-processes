from libsbml import *


def create_sbml_model(article_info):
    document = SBMLDocument(3, 1)
    model = document.createModel()
    model.setId(article_info['title'])
    model.setName(article_info['title'])

    # Example: Add compartments, species, and reactions based on the article info
    compartment = model.createCompartment()
    compartment.setId('cell')
    compartment.setSize(1)
    compartment.setConstant(True)

    species = model.createSpecies()
    species.setId('X')
    species.setCompartment('cell')
    species.setInitialAmount(10)
    species.setBoundaryCondition(False)
    species.setConstant(False)

    reaction = model.createReaction()
    reaction.setId('reaction1')
    reaction.setReversible(False)

    reactant = reaction.createReactant()
    reactant.setSpecies('X')
    reactant.setStoichiometry(1)
    reactant.setConstant(True)

    product = reaction.createProduct()
    product.setSpecies('Y')
    product.setStoichiometry(1)
    product.setConstant(True)

    return document
