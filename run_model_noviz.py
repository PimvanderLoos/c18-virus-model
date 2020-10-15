import argparse

from virus_model import *

parser = argparse.ArgumentParser(description='Run the model using the provided parameters')
parser.add_argument('output', type=str, help="The output directory for the results")
parser.add_argument('--num_agents', type=int, help="The number of agents to use", default=DEFAULT_NUM_AGENTS)
parser.add_argument('--mitigation', type=str, help="The mitigation method to use", default=DEFAULT_MITIGATION)
parser.add_argument('--baseInfection', type=int, help="The base infection chance (i.e. the probability of an agent to "
                                                      "start out as infected)", default=DEFAULT_BASE_INFECTION_CHANCE)
parser.add_argument('--spreadChance', type=int, help="The chance of the virus spreading to agents within range per "
                                                     "tick (15 min)", default=DEFAULT_SPREAD_CHANCE)
parser.add_argument('--spreadDistance', type=int, help="The maximum distance between two agents for them to be able "
                                                       "to infect each other", default=DEFAULT_SPREAD_DISTANCE)
parser.add_argument('--testChance', type=int, help="The daily chance of getting tested",
                    default=DEFAULT_DAILY_TEST_CHANCE)
parser.add_argument('--stepCount', type=int, help="The number of steps to simulate", default=1000)

args = parser.parse_args()

# Completely arbitrary value
minimum_step_count = 10
if args.stepCount < minimum_step_count:
    raise ValueError("Please select at least {} steps.".format(minimum_step_count))

print("Running with settings: \n"
      "Output dir: {}\n"
      "Num agents: {}\n"
      "Mitigation: {}\n"
      "Base infection: {}\n"
      "Spread chance: {}\n"
      "Spread distance: {}\n"
      "Daily test chance: {}\n"
      "Number of steps: {}\n"
      .format(args.output,
              args.num_agents,
              args.mitigation,
              args.baseInfection,
              args.spreadChance,
              args.spreadDistance,
              args.testChance,
              args.stepCount))

model = VirusModel(args.num_agents, DEFAULT_GRID_WIDTH, DEFAULT_GRID_HEIGHT, args.baseInfection,
                   args.spreadDistance, args.spreadChance, args.testChance, args.mitigation)

for step in range(0, args.stepCount):
    model.step()



