from mesa.visualization.modules import ChartModule

from virus_model.modular_server import CustomModularServer
from virus_model.model import VirusModel, time_element, plot_title1, plot_title2, plot_title3, plot_title4, model_params, create_canvas_room_grid

grid_canvas = create_canvas_room_grid()
chart = ChartModule([{"Label": "infected",
                      "Color": "Black"},
                     {"Label": "deaths",
                      "Color": "Red"},
                     {"Label": "quarantined",
                      "Color": "Yellow"}],
                    data_collector_name='datacollector')
chart_disease_state = ChartModule([{"Label": "just infected",
                                    "Color": "rgba(0,0,255,1)"},
                                   {"Label": "testable",
                                    "Color": "rgba(255,0,212,1)"},
                                   {"Label": "infectious",
                                    "Color": "rgba(255,0,0,1)"},
                                   {"Label": "symptomatic",
                                    "Color": "rgba(102,0,0,1)"},
                                   {"Label": "recovered",
                                    "Color": "rgba(8,323,222,1)"},
                                   {"Label": "deaths",
                                    "Color": "Brown"}
                                   ],
                                  # include healthy? {"Label": "healthy", "Color": "rgba(43,255,0,1)"},
                                  data_collector_name='datacollector')
chart_quarantined = ChartModule([{"Label": "quarantined: infected",
                                  "Color": "Green"},
                                 {"Label": "quarantined: healthy",
                                  "Color": "Yellow"},
                                 {"Label": "not quarantined: infected",
                                  "Color": "Red"}],
                                data_collector_name='datacollector')
chart_testing = ChartModule([{"Label": "tested total",
                              "Color": "Black"},
                             {"Label": "tested pending",
                             "Color":"Yellow"},
                             {"Label": "tested negative",
                              "Color": "Blue"},
                             {"Label": "tested positive",
                              "Color": "Red"}],
                            data_collector_name='datacollector')

model_params['grid_canvas'] = grid_canvas
server = CustomModularServer(VirusModel,
                             [time_element, grid_canvas, plot_title1, chart, plot_title2, chart_disease_state, plot_title3, chart_quarantined, plot_title4, chart_testing],
                             "Virus Model", model_params)

server.port = 8546
server.launch()
