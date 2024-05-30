from typing import Tuple

import numpy as np


def infer_slice(t: np.ndarray, output_start_time: int, tol: float = 0.9) -> tuple[int, int]:
    slice_start_index = 0
    slice_end_index = 0
    for i, n in enumerate(t):
        if output_start_time - tol <= round(n) <= output_start_time + tol:
            slice_start_index = i - 1
        if n == t[-1]:
            slice_end_index = i + 1
    return (slice_start_index, slice_end_index)
