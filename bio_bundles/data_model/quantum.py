import numpy as np


class DiracNotation(np.ndarray):
    def __new__(cls, values: list[complex]):
        return np.asarray(values).view(cls)


class Bra(DiracNotation):
    pass


class Ket(DiracNotation):
    def bra(self) -> Bra:
        ket_value = self.view()
        return Bra(np.conj(ket_value).T)


class XYZElements(list):
    pass


class XYZAtom(str):
    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)

    @property
    def elements(self, unique: bool = False) -> XYZElements:
        items = self.split()
        elements = XYZElements([line[0] for line in [ln.strip() for ln in self.split(";")]])
        return list(set(elements)) if unique else elements


