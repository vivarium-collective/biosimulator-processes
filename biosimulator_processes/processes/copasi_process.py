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


# 3. Update constructor conditionally
# 4. Devise parameter scan --> create Step() implementation that creates copasi1, 2, 3...
    # and provides num iterations and parameter in model_changes


class CopasiProcess(Process):
    """
        Entrypoints:

            A. SBML model file
            B. Reactions (name: {scheme: reaction contents(also defines species))
            C. Model search term (load preconfigured model from BioModels)

        Optional Parameters:

            A. 'model_changes', for example could be something like:
                'model_changes': {
                    'species_name': {
                        'name': 'A',
                        'initial_concentration': 22.24
                            ^ Here, the model changes would be applied after model instatiation in the constructor
            B. 'solver', changes the algorithm(s) used to solve the model
            C. 'units', (tree): quantity, volume, time, area, length

    """
    config_schema = {
        'model_file': 'string',
        'reactions': {
            'reaction_name': {
                'scheme': 'string'
            },
        },
        'model_search_term': 'string',
        'model_changes': 'tree[string]',
        'solver': 'string'
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

        # TODO: Update set/get with optional config params and make logic

        if self.config.get('model_file'):
            self.copasi_model_object = load_model(
                self.config['model_file'])
            self.reaction_list = get_reactions(
                model=self.copasi_model_object).index.tolist()
        elif self.config.get('model_search_term'):
            self.copasi_model_object = self.fetch_biomodel(term=self.config['model_search_term'])
        else:
            self.copasi_model_object = new_model(
                name='CopasiProcess Model')

        if self.config.get('reactions'):
            for reaction_name, reaction_spec in self.config['reactions'].items():
                add_reaction(name=reaction_name,
                             scheme=reaction_spec['scheme'])


        # Get the species (floating only)  TODO: add boundary species
        self.floating_species_list = get_species(
            model=self.copasi_model_object).index.tolist()
        self.floating_species_initial = get_species(model=self.copasi_model_object)[
            'concentration'].tolist()

        # Get the list of parameters and their values
        self.model_parameters_list = get_parameters(
            model=self.copasi_model_object).index.tolist()
        self.model_parameter_values = get_parameters(model=self.copasi_model_object)[
            'initial_value'].tolist()

        # Get a list of reactions
        self.reaction_list = get_reactions(model=self.copasi_model_object).index.tolist()

        # Get a list of compartments
        self.compartments_list = get_compartments(
            model=self.copasi_model_object).index.tolist()

    @staticmethod
    def fetch_biomodel(term: str, index: int = 0):
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
            intervals=1,
            update_model=True,
            model=self.copasi_model_object)

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
    return results
