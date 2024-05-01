"""Data Model Root for Biosimulator Processes

author: Alex Patrie < alexanderpatrie@gmail.com >
license: Apache 2.0
created: 03/2024
"""


from dataclasses import dataclass, asdict


@dataclass
class _BaseClass:
    def to_dict(self):
        return asdict(self)
