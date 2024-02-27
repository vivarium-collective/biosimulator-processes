"""Biosimulator process for Copasi/Basico."""


from basico import (
    load_model,
    get_species,
    get_parameters,
    get_reactions,
    set_species,
    run_time_course,
    get_compartments,
    new_model,
    add_reaction,
    model_info,
    load_model_from_string,
    biomodels
)
from process_bigraph import Process, Composite, pf

# 1. Map config_schema params to SEDML syntax/semantics (ie: 'model_file')
# 2. Check if/how units are addressed in SEDML
# 3. Devise parameter scan --> create Step() implementation that creates copasi1, 2, 3...
    # and provides num iterations and parameter in model_changes

# define config schema type decs here


# TODO put in utils / SED-related
def _fetch_biomodel(term: str, index: int = 0):
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


class CopasiProcess(Process):
    """
        Entrypoints:

            A. SBML model file
            B. Reactions (name: {scheme: reaction contents(also defines species))
            C. Model search term (load preconfigured model from BioModels)

        Optional Parameters:

            A. 'model_changes', for example could be something like:
                'model_changes': {
                    'species': {
                        'name': {
                            unit
                            initial_concentration
                            initial_particle_number
                            initial_expression
                            expression
                    'global_parameters': { <-- this is done with set_parameters(PARAM, kwarg=).
                        name: {
                            initial_value
                            initial expression
                            expression
                            status
                            type (fixed, assignment, reactions)
                    },'
                    'reactions': {
                        'name': {
                            'parameters': {
                                name: new value  <-- this is done with set_reaction_parameters(name="(NAME).PARAM", value=)
                            },
                            'scheme': 'string'  <-- this is done like set_reaction(name = 'R1', scheme = 'S + E + F = ES')
                        }
                    }


                            ^ Here, the model changes would be applied after model instatiation in the constructor
            B. 'solver', changes the algorithm(s) used to solve the model
            C. 'units', (tree): quantity, volume, time, area, length

        Justification:

            As per SEDML v4 specifications (section2.2.4), p.32:sed-ml-L1V4 ->

                The Model class definesthemodelsusedinasimulationexperiment(Figure2.9).
                Each instanceof theModel classhas the requiredattributesid, source, andlanguage,
                theoptional attributename,andtheoptionalchildlistOfChanges.
                Thelanguageattributedefinestheformatthemodel isencodedin. TheModel
                classreferstotheparticularmodelof interestthroughthesourceattribute.Therestrictions
                onthemodel referenceare ˆ Themodelmustbeencodedinawell-definedformat. ˆ
                Torefertothemodelencodinglanguage,areferencetoavaliddefinitionof that
                formatmustbe given(languageattribute). ˆ Torefer toaparticularmodel
                inanexternal resource, anunambiguous referencemustbegiven (sourceattribute).
    """
    # TODO: map this to SED syntax
    config_schema = {
        'model': {
            'model_id': 'string',  # could be used as the BioModels id
            'model_source': 'string',  # could be used as the "model_file" below
            'model_language': {  # could be used to load a different model
                '_type': 'string',
                '_default': 'sbml'
            },
            'model_name': 'string',
            'model_changes': 'tree[string]'  # could be used as model changes
        },
        'model_file': 'string',
        'reactions': 'tree[string]',
        'biomodel_id': 'string',
        'model_changes': 'tree[string]',  # TODO: make this more specific(what does this look like in SEDML?)
        'solver': {
            '_type': 'string',
            '_default': 'lsoda'
        }
        # units:: check sedml
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

        model_file = self.config.get('model_file')
        biomodel_id = self.config.get('biomodel_id')

        assert not (model_file and biomodel_id), 'You can only pass either a model_file or a biomodel_id.'

        # enter with model_file
        if model_file:
            self.copasi_model_object = load_model(self.config['model_file'])
        # enter with specific search term for a model
        elif biomodel_id:
            self.copasi_model_object = fetch_biomodel(model_id=self.config['biomodel_id'])
        # enter with a new model
        else:
            self.copasi_model_object = new_model(name='CopasiProcess Model')

        # add reactions 
        if self.config.get('reactions'):
            for reaction_name, reaction_spec in self.config['reactions'].items():
                add_reaction(
                    name=reaction_name,
                    scheme=reaction_spec,
                    model=self.copasi_model_object
                )

        # self.model_changes =
        # Get the species (floating only)  TODO: add boundary species
        self.floating_species_list = get_species(model=self.copasi_model_object).index.tolist()
        self.floating_species_initial = get_species(model=self.copasi_model_object)['concentration'].tolist()

        # Get the list of parameters and their values
        self.model_parameters_list = get_parameters(model=self.copasi_model_object).index.tolist()
        self.model_parameter_values = get_parameters(model=self.copasi_model_object)['initial_value'].tolist()

        # Get a list of reactions
        self.reaction_list = get_reactions(model=self.copasi_model_object).index.tolist()
        if not self.reaction_list:
            raise AttributeError('You must provide either a model filepath, a biomodel id, or reaction definitions.')

        # Get a list of compartments
        self.compartments_list = get_compartments(model=self.copasi_model_object).index.tolist()

        if self.config.get('solver'):
            pass

    def initial_state(self):
        floating_species_dict = dict(
            zip(self.floating_species_list, self.floating_species_initial))
        model_parameters_dict = dict(
            zip(self.model_parameters_list, self.model_parameter_values))
        return {
            'time': 0.0,
            'floating_species': floating_species_dict,
            'model_parameters': model_parameters_dict
        }

    def inputs(self):
        floating_species_type = {
            species_id: {
                '_type': 'float',
                '_apply': 'set',
            } for species_id in self.floating_species_list
        }
        return {
            'time': 'float',
            'floating_species': floating_species_type,
            'model_parameters': {
                param_id: 'float' for param_id in self.model_parameters_list},
            'reactions': {
                reaction_id: 'float' for reaction_id in self.reaction_list},
        }

    def outputs(self):
        floating_species_type = {
            species_id: {
                '_type': 'float',
                '_apply': 'set',
            } for species_id in self.floating_species_list
        }
        return {
            'time': 'float',
            'floating_species': floating_species_type
        }

    def update(self, inputs, interval):
        # set copasi values according to what is passed in states
        for cat_id, value in inputs['floating_species'].items():
            set_species(name=cat_id, initial_concentration=value,
                        model=self.copasi_model_object)

        # run model for "interval" length; we only want the state at the end
        timecourse = run_time_course(
            start_time=inputs['time'],
            duration=interval,
            # intervals=1,
            update_model=True,
            model=self.copasi_model_object)
            #method=self.config['solver'])

        # extract end values of concentrations from the model and set them in results
        results = {'time': interval}
        results['floating_species'] = {
            mol_id: float(get_species(name=mol_id, exact=True,
                          model=self.copasi_model_object).concentration[0])
            for mol_id in self.floating_species_list}

        return results


def test_process():
    initial_sim_state = {
        'copasi': {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model_file': 'biosimulator_processes/model_files/Caravagna2010.xml'
            },
            'inputs': {
                'floating_species': ['floating_species_store'],
                'model_parameters': ['model_parameters_store'],
                'time': ['time_store'],
                'reactions': ['reactions_store']
            },
            'outputs': {
                'floating_species': ['floating_species_store'],
                'time': ['time_store'],
            }
        },
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    'floating_species': 'tree[float]',
                    'time': 'float',
                },
            },
            'inputs': {
                'floating_species': ['floating_species_store'],
                'time': ['time_store'],
            }

        }
    }

    workflow = Composite({
        'state': initial_sim_state
    })
    workflow.run(10)
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')
    assert ('emitter',) in results.keys(), "This instance was not properly configured with an emitter."
