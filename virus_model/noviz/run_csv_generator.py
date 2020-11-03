"""
This class allows you to create a CSV file of several statistics from multiple runs.

Every run should be in its own folder and all those folders should be in one shared folder. Then just run this class
and give it the shared folder as argument. It'll then generate the CSV file for you.
"""

import argparse
import inspect
import os
import sys
from pathlib import Path
from typing import List

import pandas as pd

# Add the files from the super modules, so we can import get_directory from util.
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = Path(current_dir)
sys.path.insert(0, str(parent_dir.parent.parent))

# from virus_model.util import get_directory
from virus_model.util import get_directory
from virus_model.noviz.constants import MODEL_DATA_PATH


class Statistic:
    """
    Represents a statistic that can parse the generated data into a single entry for the final CSV file.
    """
    def __init__(self, name: str, function):
        """
        :param name: The name of this statistic. The name is used as the column name in the final CSV file.
        :param function: The function reference or lambda that can parse the data into a single value for the CSV file.

        Lambda example:
        Given a data set 'data':
        => Statistic('name', lambda data: data[['infected']].max())

        function ref example:
        Given a data set 'data' and the following method:
          def stat_method(data):
              return data[['infected']].max()

        => Statistic('name', stat_method)
        """
        self.__name = name
        self.__function = function

    def get_name(self) -> str:
        """
        Gets the name of this statistic. The name is used as the column name in the CSV file.

        :return: The name of this statistic.
        """
        return self.__name

    def get_result(self, data: pd.DataFrame):
        """
        Parses the data into a single entry for the CSV file.

        :param data: The data from an experiment.
        :return: The single entry for the CSV file.
        """
        return self.__function(data)


class StatisticManager:
    """
    Represents a set of statistics to be generated from an experiment.
    """
    def __init__(self):
        self.__statistics: List[Statistic] = []
        self.__data = [[]]

    def register_statistic(self, statistic: Statistic) -> None:
        """
        Registers a new `Statistic`.
        """
        self.__statistics.append(statistic)

    def parse_input(self, data: pd.DataFrame, file_name: str) -> None:
        """
        Parses the input using the list of registered statistics.

        :param data: The data of an experiment.
        :param file_name: The name of the folder the pickle file was read from.
        This will be used as the value in the names column of the CSV file.
        """
        row = [file_name]
        [row.extend(stat.get_result(data)) for stat in self.__statistics]
        self.__data.append(row)

    def write_csv(self, file: str) -> None:
        """
        Writes the results to the final CSV file.

        Make sure that you parse some input before writing the results! See `parse_input`.

        :param file: The CSV file.
        """
        field_names = ["name"]
        field_names.extend([stat.get_name() for stat in self.__statistics])

        # Delete the first row, because it's always empty.
        data = pd.DataFrame(self.__data, columns=field_names).iloc[1:]
        data.to_csv(file, index_label="id")


def main(raw_args=None):
    parser = argparse.ArgumentParser(description='Generates a CSV containing various statistics from multiple runs.')
    parser.add_argument('input', type=str, help="The int directory containing multiple subdirectories with results",
                        default=".")
    args = parser.parse_args(raw_args)

    directory = get_directory(args.input)

    statistics_manager = StatisticManager()
    statistics_manager.register_statistic(Statistic("Death count", lambda data: data[['deaths']].iloc[-1]))
    statistics_manager.register_statistic(Statistic("Total infected",
                                                    lambda data: pd.DataFrame(data['deaths'] + data['infected'] +
                                                    data['recovered']).iloc[-1]))
    statistics_manager.register_statistic(Statistic("Total tests", lambda data: data[['tested total']].iloc[-1]))
    statistics_manager.register_statistic(Statistic("Positive Tests", lambda data: data[['tested positive']].iloc[-1]))
    statistics_manager.register_statistic(Statistic("Negative Tests", lambda data: data[['tested negative']].iloc[-1]))
    statistics_manager.register_statistic(Statistic("Peak Infected", lambda data: data[['infected']].max()))
    statistics_manager.register_statistic(Statistic("Peak Quarantined", lambda data: data[['quarantined']].max()))

    statistics_manager.register_statistic(Statistic("Peak Infected Quarantined", lambda data: data[['quarantined: infected']].max()))
    statistics_manager.register_statistic(Statistic("Peak Healthy Quarantined", lambda data: data[['quarantined: healthy']].max()))
    statistics_manager.register_statistic(Statistic("Peak Infected Not Quarantined", lambda data: data[['not quarantined: infected']].max()))
    statistics_manager.register_statistic(Statistic("Peak Difference Healthy to Infected Quarantined",
                                                    lambda data: pd.DataFrame(data['quarantined: healthy']-data['quarantined: infected']).max()))



    count = 0
    for entry in os.scandir(directory):
        if not entry.is_dir():
            continue

        model_data = entry.path + os.sep + MODEL_DATA_PATH
        if not os.path.exists(model_data):
            continue

        count += 1
        statistics_manager.parse_input(pd.read_pickle(model_data), entry.name)

    # If no results were found at all, remind the user how to use this script and abort.
    if count == 0:
        print('''
    No results were found! Did you select the right folder?
    In the following example directory layout, you should've selected 'the_top_dir':

      the_top_dir
      |- experiment_1
      |  |- model.pickle
      |- experiment_2
      |  |- model.pickle
    ''')
        exit(0)

    csv_file = directory + os.sep + "output.csv"
    statistics_manager.write_csv(csv_file)


if __name__ == '__main__':
    main()
