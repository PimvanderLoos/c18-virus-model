#!/bin/bash

# TODO: Perhaps allow specifying an output dir?
# TODO: Multithreading to speed things up a bit?

output_dir="output"

if [[ ! $1 ]]
then
    echo "Usage: $0 <file>"
    exit 0
fi

if [[ ! -f "$1" ]]
then
    echo "File \"$1\" does not exist!"
    exit 0
fi

# If venv is used, make sure to activate it.
[[ -d "venv" ]] && source venv/bin/activate

run_experiment() {
#    $(python run_model_noviz.py "$1")
    python run_model_noviz.py "$output_dir/"$1
}

generate_stats() {
    python noviz/run_csv_generator.py "$1"
}

while read line
do
    # Skip comments
    [[ "$line" =~ ^#.*$ ]] && continue
    # Skip empty lines
    [[ ${line:-null} = null ]] && continue

#    escaped=$(echo "$line" | sed "s/\"/\\\\\"/g")
#    run_experiment "$escaped"
    run_experiment "$line"
done < "$1"

generate_stats "$output_dir"



