import argparse
import sys

from fourier.plot import build_visualization
from fourier.series import FourierSeries


def main() -> None:
    parser = argparse.ArgumentParser(
        "fourier",
        description="Animation of a Fourier series recreation of an SVG file",
        epilog="The SVG file must be made of only one path",
    )
    parser.add_argument("svg", help="path to the SVG file")
    parser.add_argument("--coeffs", type=int, default=80, help="number of coefficients in the Fourier series")
    parser.add_argument("--skip_animation", action="store_true", help="do not build the animation, only the final PNG")
    args = parser.parse_args()

    fourier_series = FourierSeries(n_coefficients=args.coeffs, filename=args.svg)
    build_visualization(fourier_series, args.skip_animation)


if __name__ == "__main__":
    sys.exit(main())
