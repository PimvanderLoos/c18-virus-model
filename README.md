# c18-virus-model
DMAS Project 20/21

Code for the implementation of our project called 'Contact Tracing in Virus Models' for the course 'Design of Multi-agents Systems'. The code uses Mesa, the Apache2 licensed agent-based modeling framework in Python.

### Summary
The model simulates the spread of SARS-CoV-2 in the setting of a university using either not mitigation strategies or contact tracing. <br>
Every agent in the model follows their own schedule which defines when they have to sit in which room. 

Every day in the model simulates 8 hours, split into 4 2-hour lecture slots. Because this model only looks at the spread of the virus in the setting of a university, the remaining 16 hours and the weekends are not modeled, though they do count towards time-based variables such as disease progression.

Once an agent is infected, they go through several stages: Infected -> Testable -> Infectious -> Symptomatic. </br>
Once an agent becomes testable (including later stages), their tests can return a positive result. Once an agent becomes infectious (including later stages) they can infect other agents. After the symptomatic stage agents will either die or recover. Once recovered, they can not get infected again. 

## Running the model
1) Install Mesa and its dependencies:
```shell
$ pip install -r https://github.com/PimvanderLoos/c18-virus-model/blob/master/requirements.txt
```

2) Clone the online repository:
```shell
$ git clone https://github.com/PimvanderLoos/c18-virus-model.git
```

3) Run the program (from Master branch)
```shell
$ python run_model.py
```

The visualization should open in a new browser window. 

### The visualization

![Model Visualization](/screenshots/model_visualization.png)

The image above shows what the model looks like. The big rectangle at the top is the break room, where agents go to when they have a break in their schedule. The squares below that are the lecture rooms, with the colored squares representing the seats.

The different colors of the agents represent their disease states, as further explained in the legend.



## Run multiple experiments
To run multiple experiments, we provide a way to run the model without its visualization. 

1) Define/Review the list of experiments to run in `bulk_experiments.txt`. 
This file contains one experiment definition per line using the commandline arguments of the `run_model_noviz` module.<br/>
Here is an example of 2 experiment definitions, one without any mitigation strategies and one that uses contact tracing:
```shell script
simulation_output_no_mitigation --stepCount 2000 --mitigation "No measures" --num_agents 800 --baseInfection 3 --spreadChance 8 --spreadDistance 2 --testDelay 5 --random-seed 42 --write-plots --room_size 15 --room_count 10 --break_room_size 22
simulation_output_contact_tracing --stepCount 2000 --mitigation "Contact Tracing" --num_agents 800 --baseInfection 3 --spreadChance 8 --spreadDistance 2 --testDelay 5 --random-seed 42 --write-plots --room_size 15 --room_count 10 --break_room_size 22
```

2) Run the experiments:
```shell
$ python noviz/run_bulk_experiments.py bulk_experiments.txt
```

3) The results can be found in `output.csv`, which will give you the following statistics about each run:
- Death count.
- Total number of agents that got infected during the simulation.
- Total number of tests performed (and whether they are negative or positive).
- The peak number of infected agents.
- The peak number of quarantined agents (and whether they are healthy or infected).
- The peak number of infected agents that were <i>not</i> quarantined.
- The peak difference in number of healhty quarantined agents compared to infected quarantined agents.
