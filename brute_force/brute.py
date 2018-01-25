#import networkx as nx #-> https://networkx.github.io/documentation/networkx-1.7/tutorial/tutorial.html
import matplotlib.pyplot as plt
import sys
import igraph
from igraph import *
import os
os.path.basename(os.path.dirname(os.path.realpath(__file__)))
import queue

# style parameters
UNTOUCHED_COLOR = "#A9A9A9"
UNTOUCHED_STATUS = 0
PROTECTED_COLOR = "#00FFFF"
PROTECTED_STATUS = 1
RISK_COLOR = "#FFFF00"
RISK_STATUS = 2
BURNING_COLOR = "#FF0000"
BURNING_STATUS = 3

import logging
logger = logging.getLogger('hsp-ff-brute')
hdlr = logging.FileHandler('brute.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

def get_temp_folder(exp_id):
    try:
        path = os.path.realpath(__file__)
        dirPath = os.path.dirname(path) + '/output/' + exp_id
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        return dirPath
    except Exception as e:
        print(e)

def get_sim_id(a,b,c,d):
    return '_'.join([str(a), str(b), str(c), str(d)])

def save_simulation(id, folder_sim, speed=1):
    file = id + '_sim.mp4'
    cmd = "ffmpeg -r " + str(speed) + " -i " + folder_sim + "out%d.png -pix_fmt yuv420p -vcodec libx264 -y " + folder_sim + "/" + file
    print(cmd)
    os.system(cmd)

def set_style(g):
    # set graph style
    g.es["width"] = 2
    g.vs["color"] = [UNTOUCHED_COLOR for v in g.vs]
    g.vs["size"] = 25
    g.vs["label_size"] = 12
    g.vs["label"] = [v.index for v in g.vs]
    g.vs["status"] = [UNTOUCHED_STATUS for v in g.vs]
    layout = g.layout_lgl()
    visual_style = {}
    visual_style["layout"] = layout
    visual_style["margin"] = [20, 20, 20, 20]
    visual_style["bbox"] = (1024, 900)
    #visual_style["keep_aspect_ratio"] = True
    return visual_style

def to_protect(g, q_risk, q_protected, tot):
    if q_risk.empty() is True:
        raise Exception('this should not occur')
    for i in range(tot):
        i = q_risk.get()
        g.vs[i]["color"] = PROTECTED_COLOR
        g.vs[i]["status"] = PROTECTED_STATUS
        q_protected.put(i)

def to_burn(g, q_risk, q_burning, tot):
    if q_risk.empty() is True:
        raise Exception('this should not occur')
    for i in range(tot):
        i = q_risk.get()
        g.vs[i]["color"] = BURNING_COLOR
        g.vs[i]["status"] = BURNING_STATUS
        q_burning.put(i)

def print_report(n, g, i, b, r, p, bu, tot_untouched):
    logger.info('==== Final Report ====')
    logger.info('grid (NxN) = ' + str(n))
    logger.info('budget = ' + str(bu))
    logger.info('tot. vertices = ' + str(g))
    logger.info('tot. iteration = ' + str(i))
    logger.info('tot. untouched = ' + str(tot_untouched))
    logger.info('tot. in risk = ' + str(len(r.queue)))
    logger.info('tot. burning = ' + str(len(b.queue)))
    logger.info('tot. protected = ' + str(len(p.queue)))

def print_state(i, b, r, p, bl, bc, bi):
    logger.debug('---------------------')
    logger.debug('iteration = ' + str(i))
    logger.debug('budget left = {0:.2f}'.format(bl))
    logger.debug('budget current tot = {0:.2f}'.format(bc))
    logger.debug('budget current = {0:.2f}'.format(bi))
    logger.debug('burning = ' + str(len(b.queue)))
    logger.debug('in risk = ' + str(len(r.queue)))
    logger.debug('protected = ' + str(len(p.queue)))
    #print('burning = ', [z for z in b.queue])
    #print('in risk = ', [z for z in r.queue])
    #print('protected = ', [z for z in p.queue])


def simulate(n, g, budget, burns, B_cells, expid, folder_sim):
    # set style
    visual_style = set_style(g)
    q_burning = queue.Queue()
    q_risk = queue.Queue()
    q_protected = queue.Queue()

    # state 0
    for v in B_cells:
        g.vs[v]["status"] = BURNING_STATUS
        g.vs[v]["color"] = BURNING_COLOR
        q_burning.put(v)

    for vb in q_burning.queue:
        for v_risk in g.neighbors(vb):
            if g.vs[v_risk]["status"] == UNTOUCHED_STATUS:
                g.vs[v_risk]["status"] = RISK_STATUS
                g.vs[v_risk]["color"] = RISK_COLOR
                q_risk.put(v_risk)

    budget_left = 0
    budget_current = budget + budget_left
    budget_i = math.floor(budget_current)

    print_state(0, q_burning, q_risk, q_protected, budget_left, budget_current, budget_i)

    # plot state 0
    plot(g, **visual_style, target=folder_sim  + 'out0.png')

    if q_risk.empty() is True:
        raise Exception('this should not occur')
    for i in range(budget_i):
        i = q_risk.get()
        g.vs[i]["color"] = PROTECTED_COLOR
        g.vs[i]["status"] = PROTECTED_STATUS
        q_protected.put(i)

    print_state(1, q_burning, q_risk, q_protected, budget_left, budget_current, budget_i)

    # plot state 1
    plot(g, **visual_style, target=folder_sim + 'out1.png')

    budget_left = budget_current - budget_i
    iter = 2

    # update: burn, update risks and protect

    while not q_risk.empty():
        # burns and update risks
        for i in range(burns - 1):
            irisk = q_risk.get()
            g.vs[irisk]["color"] = BURNING_COLOR
            g.vs[irisk]["status"] = BURNING_STATUS
            q_burning.put(irisk)
            for i_new_risks in g.neighbors(irisk):
                if g.vs[i_new_risks]["status"] == UNTOUCHED_STATUS:
                    g.vs[i_new_risks]["color"] = RISK_COLOR
                    g.vs[i_new_risks]["status"] = RISK_STATUS
                    q_risk.put(i_new_risks)
        # protect
        for i in range(budget_i - 1):
            if not q_risk.empty():
                irisk = q_risk.get()
                g.vs[irisk]["color"] = PROTECTED_COLOR
                g.vs[irisk]["status"] = PROTECTED_STATUS
                q_protected.put(irisk)

        print_state(iter, q_burning, q_risk, q_protected, budget_left, budget_current, budget_i)
        plot(g, **visual_style, target=folder_sim + 'out' + str(iter) + '.png')

        iter +=1
        budget_current = budget + budget_left
        budget_i = math.floor(budget_current)
        budget_left = budget_current - budget_i

    tot_untouched = len([v for v in g.vs["status"] if (g.vs[v]["status"] == UNTOUCHED_STATUS)])
    print_report(n, len(g.vs), iter, q_burning, q_risk, q_protected, budget, tot_untouched)

def main(argv):
    v = 4
    g = Graph.Lattice([v,v], nei=1, directed=False, mutual=True, circular=False)
    g.layout_grid(0, 0, dim=2)
    budget = 1.6
    burns = 2
    B_cells = [3,4]
    speed = 2
    exp_id = get_sim_id(v, budget, burns, len(B_cells))
    folder_sim = get_temp_folder(exp_id) + '/'
    simulate(v, g, budget, burns, B_cells, exp_id, folder_sim)
    save_simulation(exp_id, folder_sim, speed)

if __name__ == "__main__":
    main(sys.argv[1:])