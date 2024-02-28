from basico import biomodels, load_model_from_string


def fetch_biomodel_by_term(term: str, index: int = 0):
    """Search for models matching the term and return an instantiated model from BioModels.

        Args:
            term:`str`: search term
            index:`int`: selector index for model choice

        Returns:
            `CDataModel` instance of loaded model.
        TODO: Implement a dynamic search of this
    """
    models = biomodels.search_for_model(term)
    model = models[index]
    sbml = biomodels.get_content_for_model(model['id'])
    return load_model_from_string(sbml)


def fetch_biomodel(model_id: str):
    return biomodels.get_content_for_model(model_id)
