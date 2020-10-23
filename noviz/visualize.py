import os

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, MultipleLocator


class Visualizer:
    def __init__(self, data: pd.DataFrame, directory: str, save_file: bool = True, show_file: bool = False):
        """
        :param data: The data to visualize.
        :param directory: The directory to store the generated plots in if file saving is enabled.
        :param save_file: Whether or not to save the generated plots in the desired directory.
        :param show_file: Whether to show the generated plots after generating them (holds up the process
        until they are manually closed).
        """
        self.data = data
        self.directory = directory
        self.save_file = save_file
        self.show_file = show_file

    def __handle_result(self, name: str) -> None:
        """
        Handles a generated plot:
        If file saving is enabled, the plot will be saved.
        If file showing is enabled, the plot will be shown.

        :param name: The name of the plot. This will be used as file name is file saving is enabled.
        """
        if self.save_file:
            plt.savefig(self.directory + os.sep + name)
        if self.show_file:
            plt.show()

    def visualize_all(self) -> None:
        """
        Generates all the plots.
        """
        self.visualize_basic()
        self.visualize_disease_states()
        self.visualize_quarantined()
        self.visualize_testing()

    def visualize_basic(self) -> None:
        """
        Generates the basic plot of infected/deaths/quarantined vs time.
        """
        data = self.data[['infected', 'deaths', 'quarantined']]
        colors = ["red", "black", "gold"]
        data.plot(color=colors)

        plt.xlabel("Number of Steps")
        plt.ylabel("Number of Agents")
        plt.title("Effects on Agents' Lives vs Time")

        self.__handle_result("basic.png")

    def visualize_disease_states(self) -> None:
        """
        Generates the plot of the number of agents per disease state vs time.
        """
        data = self.data[['healthy', 'just infected', 'testable', 'infectious', 'symptomatic', 'recovered']]
        colors = ["green", "blue", "fuchsia", "red", "darkred", "darkturquoise"]
        data.plot(color=colors)

        plt.xlabel("Number of Steps")
        plt.ylabel("Number of Agents")
        plt.title("Disease Progression vs Time")

        self.__handle_result("disease_state.png")

    def visualize_quarantined(self) -> None:
        """
        Generates the plot of the number of quarantined agents vs time.
        """
        data = self.data[['quarantined: infected', 'quarantined: healthy', 'not quarantined: infected']]
        colors = ["green", "gold", "red"]
        data.plot(color=colors)

        plt.xlabel("Number of Steps")
        plt.ylabel("Number of Agents")
        plt.title("Quarantine vs time")

        self.__handle_result("quarantine.png")

    def visualize_testing(self) -> None:
        """
        Generates the plot of the number of tests (and their result) vs time.
        """
        data = self.data[['tested total', 'tested positive', 'tested negative']]
        colors = ["black", "blue", "red"]
        data.plot(color=colors)

        plt.xlabel("Number of Steps")
        plt.ylabel("Number of Tests")
        plt.title("Testing vs Time")

        self.__handle_result("testing.png")
