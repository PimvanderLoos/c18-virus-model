import argparse
import inspect
import sys

import os

# Add the files from the super module, so we can import get_directory from util.
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from noviz import run_csv_generator
import run_model_noviz


parser = argparse.ArgumentParser(description='Runs multiple experiments using different configurations and generates a CSV file.')
parser.add_argument('input_file', type=str, help="The file containing a set of experiment specifications.")

args = parser.parse_args()

input_file = args.input_file
if not os.path.exists(input_file):
    raise FileNotFoundError("Path does not exist: \"{}\"!".format(input_file))

if not os.path.isfile(input_file):
    raise NotADirectoryError("Path is not a file: \"{}\"!".format(input_file))

with open(input_file, 'r') as file:
    for line in file.readlines():
        if not line.strip() or line.startswith("#"):
            continue
        print(line)
        run_model_noviz.main(line.split())

run_csv_generator.main(["."])
