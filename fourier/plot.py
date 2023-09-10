import dataclasses
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from fourier.series import FourierSeries


@dataclasses.dataclass
class VisuSpecs:
    figsize: tuple[int, int] = (10, 10)
    scatter_size: int = 1
    duration: int = 10
    framerate: int = 30
    n_points: int = 50_000
    border: int = 100
    lw: int = 3
    last_frame_duration: int = 3
    facecolor: str = "black"
    circle_color: str = "b"
    line_color: str = "red"
    point_color: str = "white"

    def __post_init__(self) -> None:
        self.n_digits = len(str(self.framerate * self.duration + 1))
        self.n_frames = self.framerate * self.duration


def plot_final(fourier: FourierSeries, specs: VisuSpecs) -> tuple[Figure, Axes]:
    time = np.linspace(0, 1, specs.n_points)
    points = np.array([fourier(t) for t in time])
    xmin, xmax = min(points.real) - specs.border, max(points.real) + specs.border
    ymin, ymax = min(points.imag) - specs.border, max(points.imag) + specs.border

    fig, ax = plt.subplots(figsize=specs.figsize, facecolor="black")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.scatter(points.real, points.imag, s=specs.scatter_size, color="white")
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    ax.axis("off")
    return fig, ax


def create_frames(fourier: FourierSeries, specs: VisuSpecs, output: Path) -> None:
    time = np.linspace(0, 1, specs.n_points)
    points = np.array([fourier(t) for t in time])
    xmin, xmax = min(points.real) - specs.border, max(points.real) + specs.border
    ymin, ymax = min(points.imag) - specs.border, max(points.imag) + specs.border
    order = np.argsort(np.abs(fourier.coeffs))[::-1]

    def worker(idx: int, t: float) -> None:
        last_index = 0
        while last_index < specs.n_points and time[last_index] <= t:
            last_index += 1
        terms = fourier.terms(t)
        fig, ax = plt.subplots(figsize=specs.figsize, facecolor=specs.facecolor)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        current = terms[order[0]]
        for index in order[1:]:
            circle = plt.Circle(
                (current.real, current.imag), abs(terms[index]), fill=False, color=specs.circle_color, lw=specs.lw
            )
            ax.add_patch(circle)
            plt.arrow(
                current.real,
                current.imag,
                terms[index].real,
                terms[index].imag,
                width=specs.lw,
                color=specs.line_color,
                head_width=0,
            )
            current += terms[index]
        ax.scatter(points[:last_index].real, points[:last_index].imag, s=specs.scatter_size, color=specs.point_color)
        ax.set_aspect("equal", adjustable="box")
        fig.tight_layout()
        plt.close(fig)
        ax.axis("off")
        fig.savefig(output / f"frame_{idx:0{specs.n_digits}d}.png")
        plt.close(fig)

    Parallel(n_jobs=-1, verbose=5)(delayed(worker)(i, t) for i, t in enumerate(np.linspace(0, 1, specs.n_frames)))


def build_visualization(fourier: FourierSeries, skip_animation: bool) -> None:
    specs = VisuSpecs()
    out_dir = Path("./")
    fig, _ = plot_final(fourier, specs)
    fig.savefig(out_dir / "fourier.png")
    plt.close(fig)

    if skip_animation:
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copyfile(out_dir / "fourier.png", tmp_path / f"frame_{specs.n_frames:0{specs.n_digits}d}.png")
        create_frames(fourier, specs, tmp_path)
        subprocess.call(
            f"ffmpeg -y -framerate {specs.framerate} -i "
            + f"{tmp_path / f'frame_%0{specs.n_digits}d.png'} {tmp_path / 'fourier.mp4'}",
            shell=True,
        )
        subprocess.call(
            f"ffmpeg -y -i {tmp_path / 'fourier.mp4'} -vf "
            + f"tpad=stop_mode=clone:stop_duration={specs.last_frame_duration} {out_dir / 'fourier.mp4'}",
            shell=True,
        )
        subprocess.call(
            f"ffmpeg -y -i {out_dir / 'fourier.mp4'} -vf "
            + '"fps=30,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"'
            + f" -loop 0 {out_dir / 'fourier.gif'}",
            shell=True,
        )
