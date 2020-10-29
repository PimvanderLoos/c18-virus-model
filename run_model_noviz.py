import argparse

from noviz.constants import MODEL_DATA_PATH
from noviz.visualize import Visualizer
from virus_model import *

parser = argparse.ArgumentParser(description='Run the model using the provided parameters')
parser.add_argument('output', type=str, help="The output directory for the results")
parser.add_argument('--num_agents', type=int, help="The number of agents to use", default=DEFAULT_NUM_AGENTS)
parser.add_argument('--mitigation', type=str, help="The mitigation method to use", default=DEFAULT_MITIGATION)
parser.add_argument('--baseInfection', type=float, help="The base infection rate (i.e. the percentage of agents "
                                                        "starting out infected)", default=DEFAULT_BASE_INFECTION_RATE)
parser.add_argument('--spreadChance', type=int, help="The chance of the virus spreading to agents within range per "
                                                     "tick (15 min)", default=DEFAULT_SPREAD_CHANCE)
parser.add_argument('--spreadDistance', type=int, help="The maximum distance between two agents for them to be able "
                                                       "to infect each other", default=DEFAULT_SPREAD_DISTANCE)
parser.add_argument('--testDelay', type=int, help="The number of days it takes for a test result to become available ",
                    default=DEFAULT_TEST_DELAY)
parser.add_argument('--testChance', type=int, help="The daily chance of getting tested",
                    default=DEFAULT_DAILY_TEST_CHANCE)
#
parser.add_argument('--participationTracing', type=int, help="Proportion of people particpating in contact tracing",
                    default=DEFAULT_PARTICIPATION_TRACING)
parser.add_argument('--lastContactDays', type=int, help="Number of days for tracing last contacts ",
                    default=DEFAULT_LAST_CONTACT_DAYS)
parser.add_argument('--distanceTracking', type=int, help="Radius of Tracing contacts in meters",
                    default=DEFAULT_DISTANCE_TRACKING)
#
parser.add_argument('--room_size', type=int, help="The size of the rooms (this value is squared).",
                    default=DEFAULT_ROOM_SIZE)
parser.add_argument('--room_count', type=int, help="The number of class rooms",
                    default=DEFAULT_ROOM_COUNT)
parser.add_argument('--break_room_size', type=int, help="The size of the break room.",
                    default=DEFAULT_BREAK_ROOM_SIZE)
parser.add_argument('--stepCount', type=int, help="The number of steps to simulate", default=2000)
parser.add_argument('--show-plots', dest='show', help="Show the plots.", action='store_true')
parser.add_argument('--write-plots', dest='write', help="Write the plots to files", action='store_true')
parser.add_argument('--random-seed', type=int, dest='seed', help="The seed to use for the random module. This is a "
                                                                 "numerical value. Not providing a seed means random "
                                                                 "values will be used.", default=DEFAULT_RANDOM_SEED)

args = parser.parse_args()

# Completely arbitrary value
minimum_step_count = 22
if args.stepCount < minimum_step_count:
    raise ValueError("Please select at least {} steps.".format(minimum_step_count))

directory = args.output.rstrip(os.sep)
os.makedirs(directory, exist_ok=True)


settings_file = directory + os.sep + "settings.txt"
file = open(settings_file, "w+")
file.write("Running with settings: \n"
           "Output dir: {}\n"
           "Num agents: {}\n"
           "Mitigation: {}\n"
           "Base infection: {}\n"
           "Spread chance: {}\n"
           "Spread distance: {}\n"
           "Daily test chance: {}\n"
           "Number of steps: {}\n"
           "Test delay: {}\n"
           "Participation Contact Tracing: {}\n"
           "Days of Tracing Contacts: {}\n"
           "Distance of Contact Tracing: {}\n"
           "Seed: {}\n"
           "Room Size: {}\n"
           "Room Count: {}\n"
           "Break Room Size: {}\n"
           .format(directory,
                   args.num_agents,
                   args.mitigation,
                   args.baseInfection,
                   args.spreadChance,
                   args.spreadDistance,
                   args.testChance,
                   args.stepCount,
                   args.testDelay,
                   args.participationTracing,
                   args.lastContactDays,
                   args.distanceTracking,
                   args.seed,
                   args.room_size,
                   args.room_count,
                   args.break_room_size))

file.close()

model = VirusModel(args.num_agents, DEFAULT_GRID_WIDTH, DEFAULT_GRID_HEIGHT, args.baseInfection,
                   args.spreadDistance, args.spreadChance, args.testChance, args.mitigation, args.testDelay,
                   args.participationTracing, args.lastContactDays, args.distanceTracking, args.seed,
                   None, None, args.room_count, args.room_size, args.break_room_size)

for step in range(0, args.stepCount):
    model.step()

df = model.datacollector.get_model_vars_dataframe()
model_data_path = directory + os.sep + MODEL_DATA_PATH
df.to_pickle(model_data_path)

if args.show or args.write:
    Visualizer(df, directory, save_file=args.write, show_file=args.show).visualize_all()


