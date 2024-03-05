from typing import *
from process_bigraph import Step


class ParameterScan(Step):
    config_schema = {
        'process_instance'
        # 'process_instances': 'tree[object]'
    }


