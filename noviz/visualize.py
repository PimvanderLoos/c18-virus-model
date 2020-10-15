import pandas as pd
import matplotlib.pyplot as plt


class Visualizer:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def visualize_all(self):
        self.visualize_basic()
        self.visualize_disease_states()
        self.visualize_quarantined()
        self.visualize_testing()

    def visualize_basic(self):
        data = self.data[['infected', 'deaths', 'quarantined']]
        colors = ["red", "black", "gold"]
        data.plot(color=colors)
        plt.show()

    def visualize_disease_states(self):
        data = self.data[['healthy', 'just infected', 'testable', 'infectious', 'symptomatic', 'recovered']]
        colors = ["green", "blue", "fuchsia", "red", "darkred", "darkturquoise"]
        data.plot(color=colors)
        plt.show()

    def visualize_quarantined(self):
        data = self.data[['quarantined: infected', 'quarantined: healthy', 'not quarantined: infected']]
        colors = ["green", "gold", "red"]
        data.plot(color=colors)
        plt.show()

    def visualize_testing(self):
        data = self.data[['tested total', 'tested positive', 'tested negative']]
        colors = ["black", "blue", "red"]
        data.plot(color=colors)
        plt.show()
