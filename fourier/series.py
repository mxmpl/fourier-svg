import cmath
import dataclasses
import functools
import pathlib
import warnings
from typing import Any, Callable
from xml.dom import minidom

import numpy as np
from joblib import Parallel, delayed
from scipy import integrate
from svg.path import parse_path

IntegrationKwargs = dict[Any, Any]


def _complex_quadrature(func: Callable, a: float, b: float, **kwargs: IntegrationKwargs) -> complex:
    real_integral = integrate.quad(lambda x: np.real(func(x)), a, b, **kwargs)
    imag_integral = integrate.quad(lambda x: np.imag(func(x)), a, b, **kwargs)
    return real_integral[0] + 1j * imag_integral[0]


def _get_paths(filename: str, error: float) -> list[tuple[float, float]]:
    doc = minidom.parse(filename)
    path_strings = [path.getAttribute("d") for path in doc.getElementsByTagName("path")]
    doc.unlink()
    paths = []
    for path_string in path_strings:
        path = parse_path(path_string)
        for e in path:
            paths.append((e.length(error), e))
    length = sum([seg[0] for seg in paths])
    return [(seg[0] / length, seg[1]) for seg in paths]


def _build_complex_function(t: float, paths: list) -> complex:
    if t < 0 or t > 1:
        raise ValueError("Time t must be between 0 and 1")
    old_length = 0
    for length, seg in paths:
        if t <= old_length + length:  # SVG axis
            return seg.point(t - old_length).conjugate()
        old_length += length
    raise ValueError("Should not happen")


def _compute_coefficients(complex_function: Callable, n_coeffs: int, **kwargs: IntegrationKwargs) -> np.ndarray:
    def worker(n: int) -> float:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return _complex_quadrature(
                lambda t: complex_function(t) * cmath.rect(1, -2 * np.pi * t * n), 0, 1, **kwargs
            )

    return np.array(Parallel(n_jobs=-1)(delayed(worker)(n) for n in range(-n_coeffs, n_coeffs + 1)))


@dataclasses.dataclass
class FourierSeries:
    n_coefficients: int
    filename: str
    svg_error: float = 1e-2
    integration_kwargs: IntegrationKwargs = dataclasses.field(default_factory=lambda: {"limit": 200, "epsabs": 0.5})

    def __post_init__(self) -> None:
        self.n_coefficients = int(self.n_coefficients)
        if self.n_coefficients < 1:
            raise ValueError(f"Number of coefficients must be greater than 1, not {self.n_coefficients}.")

        if not pathlib.Path(self.filename).is_file():
            raise ValueError(f"File ({self.filename}) does not exist.")

        if self.svg_error <= 0:
            raise ValueError(f"SVG margin for curve length computation must be non negative, not {self.svg_error}")

        paths = _get_paths(self.filename, self.svg_error)
        function = functools.partial(_build_complex_function, paths=paths)
        self.coeffs = _compute_coefficients(function, self.n_coefficients, **self.integration_kwargs)

    def terms(self, t: float) -> np.ndarray:
        return self.coeffs * np.array(
            [cmath.rect(1, -2 * np.pi * t * n) for n in range(-self.n_coefficients, self.n_coefficients + 1)]
        )

    def __call__(self, t: float) -> complex:
        return sum(self.terms(t))
