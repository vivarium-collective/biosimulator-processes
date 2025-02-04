from abc import ABC, abstractmethod

from process_bigraph import Process


class SedProcess(Process, ABC):
    config_schema = {
        'model': 'sed_model',
        'species_context': {
            '_type': 'string',
            '_default': 'concentrations'
        },
        'method': {
            '_type': 'string',
            '_default': 'deterministic'  # <-- CVODE for consistency, or should we use LSODA?
        },
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

    @abstractmethod
    def initial_state(self):
        pass

    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass

    @abstractmethod
    def update(self, inputs, interval):
        pass


class SedUTCProcess(SedProcess):
    config_schema = {
        'model': 'TimeCourseConfig',
        'species_context': {
            '_type': 'string',
            '_default': 'concentrations'
        },
        'method': {
            '_type': 'string',
            '_default': 'deterministic'  # <-- CVODE for consistency, or should we use LSODA?
        },
        'sbml_fp': 'maybe[string]'
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

    @abstractmethod
    def initial_state(self):
        pass

    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass

    @abstractmethod
    def update(self, inputs, interval):
        pass
