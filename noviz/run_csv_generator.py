"""
This class allows you to create a CSV file of several statistics from multiple runs.

Every run should be in its own folder and all those folders should be in one shared folder. Then just run this class
and give it the shared folder as argument. It'll then generate the CSV file for you.
"""

import argparse
import os

import pandas as pd

from noviz.constants import MODEL_DATA_PATH


class Statistic:
    def __init__(self, name: str, function):
        self.__name = name
        self.__function = function

    def get_name(self):
        return self.__name

    def get_result(self, data: pd.DataFrame):
        return self.__function(data)


class StatisticManager:
    def __init__(self, ):
        self.__statistics = []
        self.__data = [[]]

    def register_statistic(self, statistic: Statistic):
        self.__statistics.append(statistic)

    def parse_input(self, data: pd.DataFrame, file_name: str):
        row = [file_name]
        [row.extend(stat.get_result(data)) for stat in self.__statistics]
        self.__data.append(row)

    def write_csv(self, file):
        field_names = ["name"]
        field_names.extend([stat.get_name() for stat in self.__statistics])

        # Delete the first row, because it's always empty.
        data = pd.DataFrame(self.__data, columns=field_names).iloc[1:]
        data.to_csv(file, index_label="id")


parser = argparse.ArgumentParser(description='Generates a CSV containing various statistics from multiple runs.')
parser.add_argument('input', type=str, help="The int directory containing multiple subdirectories with results",
                    default=".")
args = parser.parse_args()

directory = args.input.rstrip(os.sep)
if not os.path.exists(directory):
    raise ValueError("Path does not exist: \"{}\"!".format(directory))

if not os.path.isdir(directory):
    raise ValueError("Path is not a directory: \"{}\"!".format(directory))


statistics_manager = StatisticManager()
statistics_manager.register_statistic(Statistic("Death count", lambda data: data[['deaths']].iloc[-1]))
statistics_manager.register_statistic(Statistic("Total tests", lambda data: data[['tested total']].iloc[-1]))
statistics_manager.register_statistic(Statistic("Positive Tests", lambda data: data[['tested positive']].iloc[-1]))
statistics_manager.register_statistic(Statistic("Negative Tests", lambda data: data[['tested negative']].iloc[-1]))
statistics_manager.register_statistic(Statistic("Peak Infected", lambda data: data[['infected']].max()))
statistics_manager.register_statistic(Statistic("Peak Quarantined", lambda data: data[['quarantined']].max()))

for entry in os.scandir(directory):
    if not entry.is_dir():
        continue

    model_data = entry.path + os.sep + MODEL_DATA_PATH
    if not os.path.exists(model_data):
        continue

    statistics_manager.parse_input(pd.read_pickle(model_data), entry.name)

csv_file = directory + os.sep + "output.csv"
statistics_manager.write_csv(csv_file)
