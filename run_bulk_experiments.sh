#!/bin/bash

output_dir="output"

if [[ ! $1 ]]
then
    echo "Usage: $0 <file> [output_dir]"
    exit 0
fi

if [[ $2 ]]
then
    output_dir="$2"
fi

if [[ ! -f "$1" ]]
then
    echo "File \"$1\" does not exist!"
    exit 0
fi

# If venv is used, make sure to activate it.
[[ -d "venv" ]] && source venv/bin/activate

# Run an experiment with a set of arguments.
run_experiment() {
    python run_model_noviz.py "$output_dir/"$1
}

# Generate the final CSV file comparing the results of
# the experiments we just ran.
generate_stats() {
    python noviz/run_csv_generator.py "$output_dir"
}

while read -r line
do
    # Skip comments
    [[ "$line" =~ ^#.*$ ]] && continue
    # Skip empty lines
    [[ ${line:-null} = null ]] && continue

    run_experiment "$line" >> /dev/null &
done < "$1"

# Wait for all the subprocesses to finish
wait

generate_stats



