import argparse
import pandas
import inspect
import os
import sys
from typing import List

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import util
from noviz.constants import MODEL_DATA_PATH
from noviz.visualize import Visualizer

parser = argparse.ArgumentParser(description='Run the model using the provided parameters')
parser.add_argument('input', type=str, help="The input directory for the results")
parser.add_argument('--show-plots', dest='show', help="Show the plots.", action='store_true')
parser.add_argument('--write-plots', dest='write', help="Write the plots to files", action='store_true')

args = parser.parse_args()

directory = util.get_directory(args.input)

model_data_path = directory.rstrip(os.sep) + os.sep + MODEL_DATA_PATH
model_data = pandas.read_pickle(model_data_path)

if not args.write and not args.show:
    raise RuntimeError("Not showing or saving the plots... Please specify at least one action!")

Visualizer(model_data, directory, save_file=args.write, show_file=args.show).visualize_all()

