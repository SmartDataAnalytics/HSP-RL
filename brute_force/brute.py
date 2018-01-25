#import networkx as nx #-> https://networkx.github.io/documentation/networkx-1.7/tutorial/tutorial.html
import matplotlib.pyplot as plt
import sys
from igraph import *
import os
os.path.basename(os.path.dirname(os.path.realpath(__file__)))
import queue

# style parameters
UNTOUCHED_COLOR = "#A9A9A9"
UNTOUCHED_STATUS = 0
RISK_COLOR = "#FFFF00"
RISK_STATUS = 1
BURNING_COLOR = "#FF0000"
BURNING_STATUS = 2
PROTECTED_COLOR = "#0000FF"
PROTECTED_STATUS = 3

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
    g.vs["color"] = UNTOUCHED_COLOR
    g.vs["size"] = 50
    g.vs["label_size"] = 20
    g.vs["label"] = [v.index for v in g.vs]
    g.vs["status"] = [UNTOUCHED_STATUS for v in g.vs]
    layout = g.layout_lgl()
    visual_style = {}
    visual_style["layout"] = layout
    visual_style["margin"] = [30, 30, 30, 30]
    visual_style["bbox"] = (1024, 900)
    visual_style["keep_aspect_ratio"] = True
    return visual_style

def to_protect(g, q_risk, q_protected, tot):
    if q_risk.empty() is True:
        raise 'this should not occur'
    for i in range(tot):
        i = q_risk.get()
        g.vs[i]["color"] = PROTECTED_COLOR
        g.vs[i]["status"] = PROTECTED_STATUS
        q_protected.put(i)

def to_burn(g, q_risk, q_burning, tot):
    if q_risk.empty() is True:
        raise 'this should not occur'
    for i in range(tot):
        i = q_risk.get()
        g.vs[i]["color"] = BURNING_COLOR
        g.vs[i]["status"] = BURNING_STATUS
        q_burning.put(i)



def simulate(g, budget, burns, B_cells):
    # set style
    visual_style = set_style(g)

    q_burning = queue.Queue()
    q_risk = queue.Queue()
    q_protected = queue.Queue()

    # state 0
    for v in B_cells:
        g.vs[v]["color"] = BURNING_COLOR
        g.vs[v]["status"] = BURNING_STATUS
        q_burning.put(v)
        for v_risk in g.neighbors(v):
            q_risk.put(v_risk)

    budget_left = 0
    budget_current = budget + budget_left
    budget_i = math.floor(budget_current)
    budget_next_i = budget_current - budget_i

    # plot state 0
    plot(g, **visual_style, target=TEMP_PATH_SIMULATION + '/out0.png')

    to_protect(g, q_risk, q_protected, budget_i)

    # plot state 1
    plot(g, **visual_style, target=TEMP_PATH_SIMULATION + '/out1.png')

    iter = 2

    # update: burn, update risks and protect

    while not q_risk.empty():
        #burns
        for i in range(burns):
            irisk = q_risk.get()
            g.vs[irisk]["color"] = BURNING_COLOR
            g.vs[irisk]["status"] = BURNING_STATUS
            q_burning.put(irisk)
            for i_new_risks in g.neighbors(irisk):
                q_risk.put(i_new_risks)
                g.vs[i_new_risks]["color"] = RISK_COLOR
                g.vs[i_new_risks]["status"] = RISK_STATUS




        for vsn in g.neighbors(vs):
            s = g.vs[vsn]["status"]
            if s == UNTOUCHED_STATUS and i_budget_state <= accumulated_budget:
                g.vs[vsn]["color"]  = PROTECTED_COLOR
                g.vs[vsn]["status"] = PROTECTED_STATUS
                i_budget_state += 1

            if s == UNTOUCHED_STATUS and i_burned_state <= nr_vb:
                g.vs[vsn]["color"]  = BURNING_COLOR
                g.vs[vsn]["status"] = BURNING_STATUS
                i_burned_state += 1
                qv_burning.put(vsn) # next iteration should visit its neighbors



def main(argv):
    # simulation parameters
    nr_edges = 2
    nr_vertex = 10
    g = Graph.Tree(nr_vertex, nr_edges)

    budget = 1.6
    burns = 2
    B_cells = [0, 1]

    # start
    simulate(g, budget, burns, B_cells)
    # export simulation
    save_simulation()

if __name__ == "__main__":
    main(sys.argv[1:])