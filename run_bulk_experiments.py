import argparse
import os

import run_model_noviz
from virus_model.noviz import run_csv_generator

parser = argparse.ArgumentParser(
    description='Runs multiple experiments using different configurations and generates a CSV file.')
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
