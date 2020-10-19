import os

import pandas as pd
import matplotlib.pyplot as plt


class Visualizer:
    def __init__(self, data: pd.DataFrame, directory: str, save_file: bool = True, show_file: bool = False):
        self.data = data
        self.directory = directory
        self.save_file = save_file
        self.show_file = show_file

    def visualize_all(self):
        self.visualize_basic()
        self.visualize_disease_states()
        self.visualize_quarantined()
        self.visualize_testing()

    def __handle_result(self, name: str):
        if self.save_file:
            plt.savefig(self.directory + os.sep + name)
        if self.show_file:
            plt.show()

    def visualize_basic(self):
        data = self.data[['infected', 'deaths', 'quarantined']]
        colors = ["red", "black", "gold"]
        data.plot(color=colors)
        self.__handle_result("basic.png")

    def visualize_disease_states(self):
        data = self.data[['healthy', 'just infected', 'testable', 'infectious', 'symptomatic', 'recovered']]
        colors = ["green", "blue", "fuchsia", "red", "darkred", "darkturquoise"]
        data.plot(color=colors)
        self.__handle_result("disease_state.png")

    def visualize_quarantined(self):
        data = self.data[['quarantined: infected', 'quarantined: healthy', 'not quarantined: infected']]
        colors = ["green", "gold", "red"]
        data.plot(color=colors)
        self.__handle_result("quarantine.png")

    def visualize_testing(self):
        data = self.data[['tested total', 'tested positive', 'tested negative']]
        colors = ["black", "blue", "red"]
        data.plot(color=colors)
        self.__handle_result("testing.png")
