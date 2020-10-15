import argparse
import pandas
import os

# TODO: Accept seed parameter for the Random attribute of the model for reproducible results.
from noviz.constants import MODEL_DATA_PATH
from noviz.visualize import Visualizer

parser = argparse.ArgumentParser(description='Run the model using the provided parameters')
parser.add_argument('input', type=str, help="The input directory for the results")
parser.add_argument('--show-plots', dest='show', help="Show the plots.", action='store_true')
parser.add_argument('--write-plots', dest='write', help="Write the plots to files", action='store_true')

args = parser.parse_args()
directory = args.input.rstrip(os.sep)

if not os.path.exists(directory):
    raise ValueError("Path does not exist: \"{}\"!".format(directory))

if not os.path.isdir(directory):
    raise ValueError("Path is not a directory: \"{}\"!".format(directory))

model_data_path = directory.rstrip(os.sep) + os.sep + MODEL_DATA_PATH
model_data = pandas.read_pickle(model_data_path)

Visualizer(model_data, directory, save_file=args.write, show_file=args.show).visualize_all()

