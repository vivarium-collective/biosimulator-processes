from typing import Tuple, Callable, Union, List
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from process_bigraph.composite import Step


@dataclass
class PlotLabelConfig:
    title: str
    x_label: str
    y_label: str


class ResultsAnimation:
    def __init__(self,
                 x_data: np.array,
                 y_data: np.array,
                 plot_type_func: Callable,
                 plot_label_config: PlotLabelConfig,
                 **config):
        self.x_data = x_data
        self.y_data = y_data
        self.plot_type_func = plot_type_func
        self.plot_label_config = plot_label_config
        self.config = config

    def _set_axis_limits(self, ax_limit_func, data):
        return ax_limit_func(data.min(), data.max())

    def _prepare_animation(self, t):
        plt.cla()
        self.plot_type_func(
            self.x_data,
            self.y_data,
            color=self.config.get('color', 'blue')
        )

        self._set_axis_limits(plt.xlim, self.x_data)
        self._set_axis_limits(plt.ylim, self.y_data)
        plt.axhline(0, color='grey', lw=0.5)
        plt.axvline(0, color='grey', lw=0.5)
        plt.title(self.plot_label_config.title)
        plt.xlabel(self.plot_label_config.x_label)
        plt.ylabel(self.plot_label_config.y_label)

    def _create_animation_components(self) -> Tuple:
        """
        Creates a matplotlib subplot setup for animation.

        Returns:
            Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]: A tuple containing the figure and axes objects.
        """
        plt.rcParams["animation.html"] = "jshtml"
        plt.rcParams['figure.dpi'] = 150  # TODO: add this to config
        plt.ioff()
        fig, ax = plt.subplots()
        return fig, ax

    def run(self, num_frames: int):
        """
        Creates and runs the animation.

        Args:
            num_frames (int): Number of frames to animate

        Returns:
            matplotlib.animation.FuncAnimation: The animation object.
        """
        fig, ax = self._create_animation_components()
        return FuncAnimation(fig, self._prepare_animation, frames=num_frames)


# TODO: Create plotting step for this


class Plotter2d(Step):
    @classmethod
    def plot_output(
            cls,
            x_data: Union[List, np.ndarray],
            y_data: Union[List, np.ndarray],
            **label_config
    ) -> None:
        """Plot arbitrary output.

            Args:
                x_data: array or list of data for x axis.
                y_data: array or list of data for y axis.
                **label_config: kwargs include--> title, x_label, y_label
        """
        plt.figure(figsize=(8, 5))
        plt.plot(x_data, y_data, marker='o', linestyle='-', color='b', label=label_config.get('species'))
        plt.title(label_config.get('title'))
        plt.xlabel(label_config.get('x_label'))
        plt.ylabel(label_config.get('y_label'))
        plt.legend()
        plt.grid(True)
        plt.show()

    @classmethod
    def plot_single_output(
            cls,
            timescale: Union[List, np.array],
            data: Union[List, np.array],
            species_name: str,
            plot_concentration=True
    ) -> None:
        """Plotting function to plot the output of a SINGLE species' concentrations over a timescale for the output
            of a deterministic time course simulation.

            Args:
                timescale:`Union[List, np.array]`: list containing each time step.
                data:`Union[List, np.array]`: output data mapped to each timescale.
                species_name:`str`: Name of the species that you are plotting.
                plot_concentration:`bool`: Whether you are plotting concentrations for data. Effects
                    plot labels. Defaults to `True`.
        """
        plt.figure(figsize=(8, 5))
        plt.plot(timescale, data, marker='o', linestyle='-', color='b', label=species_name)
        plt.title(f'{species_name} over time')
        plt.xlabel('Time')
        plt.ylabel('Concentration' if plot_concentration else 'Counts')
        plt.legend()
        plt.grid(True)
        plt.show()


