import argparse
import pandas
import os

# TODO: Accept seed parameter for the Random attribute of the model for reproducible results.
from noviz.run_model_noviz import MODEL_DATA_PATH
from noviz.visualize import Visualizer

parser = argparse.ArgumentParser(description='Run the model using the provided parameters')
parser.add_argument('input', type=str, help="The output directory for the results")

args = parser.parse_args()

if not os.path.exists(args.input):
    raise ValueError("Path does not exist: \"{}\"!".format(args.input))

if not os.path.isdir(args.input):
    raise ValueError("Path is not a directory: \"{}\"!".format(args.input))

model_data_path = args.input.rstrip(os.sep) + MODEL_DATA_PATH
model_data = pandas.read_pickle(model_data_path)

Visualizer(model_data).visualize_all()

# plt.plot()
# plt.show()

