#import networkx as nx
import matplotlib.pyplot as plt
import sys
from igraph import *
import os
os.path.basename(os.path.dirname(os.path.realpath(__file__)))
import queue

# style parameters
UNTOUCH_COLOR = "#A9A9A9"
UNTOUCH_STATUS = 0
BURN_COLOR = "#FF0000"
BURN_STATUS = 1
SAVE_COLOR = "#00FF00"
SAVE_STATUS = 2

def get_temp_folder():
    try:
        path = os.path.realpath(__file__)
        dirPath = os.path.dirname(path) + '/temp'
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        return dirPath
    except Exception as e:
        print(e)

TEMP_PATH_SIMULATION = get_temp_folder()

def save_simulation():
    os.system("ffmpeg -r 1 -i " + TEMP_PATH_SIMULATION + "/out%d.png -vcodec mpeg4 -y " +
              TEMP_PATH_SIMULATION + "/ff_simulation.mp4")

def set_style(g):
    # set graph style
    g.es["width"] = 2
    g.vs["color"] = UNTOUCH_COLOR
    g.vs["size"] = 50
    g.vs["label_size"] = 20
    g.vs["label"] = [v.index for v in g.vs]
    g.vs["status"] = [UNTOUCH_STATUS for v in g.vs]
    layout = g.layout_lgl()
    visual_style = {}
    visual_style["layout"] = layout
    visual_style["margin"] = [30, 30, 30, 30]
    visual_style["bbox"] = (1024, 900)
    visual_style["keep_aspect_ratio"] = True
    return visual_style

def main(argv):
    # simulation parameters
    nr_edges = 2
    nr_vertex = 10
    budget = 1.6
    nr_vertex_burns_per_i = 2
    start_burning_vertices = [0]
    g = Graph.Tree(nr_vertex, nr_edges)
    # start
    simulate(g, budget, nr_vertex_burns_per_i, start_burning_vertices)
    # export simulation
    save_simulation()

def simulate(g, budget, nr_vb, start_burning_cells):
    # set style
    visual_style = set_style(g)

    q_v_burning = queue.Queue()
    q_v_risk = queue.Queue()
    q_v_saved = queue.Queue()

    for v in start_burning_cells:
        g.vs[v]["color"] = BURN_COLOR
        g.vs[v]["status"] = BURN_STATUS
        q_v_burning.put(v)
        for v_risk in g.neighbors(v):
            q_v_risk.put(v_risk)


    plot(g, **visual_style, target=TEMP_PATH_SIMULATION + '/out0.png')



    tot_moves = 0
    # current burning nodes
    nr_burning = len(nr_vb)
    nr_burning_new = 999999999999
    q_state = queue.Queue()
    q_state.put(-1)  # to enter while



    iter = 0
    accumulated_budget = 0
    i_budget_state = 0
    i_burned_state = 0

    while not qv_burning.empty():


    while not q_state.empty():
        vs = q_state.get()

        for vsn in g.neighbors(vs):
            s = g.vs[vsn]["status"]
            if s == UNTOUCH_STATUS and i_budget_state <= accumulated_budget:
                g.vs[vsn]["color"]  = SAVE_COLOR
                g.vs[vsn]["status"] = SAVE_STATUS
                i_budget_state += 1

            if s == UNTOUCH_STATUS and i_burned_state <= nr_vb:
                g.vs[vsn]["color"]  = BURN_COLOR
                g.vs[vsn]["status"] = BURN_STATUS
                i_burned_state += 1
                qv_burning.put(vsn) # next iteration should visit its neighbors









        if v == -1:


    while converge is False:
        # increase time
        t = t + 1
        # get neighbor(s) of the burning cell(s)

        # add barrier(s)

        # spread the fire to remaining vertex/vertices


        nr_burning_new = len(g.vs["status"][BURN_STATUS])


if __name__ == "__main__":
    main(sys.argv[1:])