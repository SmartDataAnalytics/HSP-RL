#import networkx as nx #-> https://networkx.github.io/documentation/networkx-1.7/tutorial/tutorial.html
import matplotlib.pyplot as plt
import sys
import igraph
from igraph import *
import os
os.path.basename(os.path.dirname(os.path.realpath(__file__)))
import queue
import logging
import itertools

dir_path = os.path.dirname(os.path.realpath(__file__))



# style parameters
UNTOUCHED_COLOR = "#A9A9A9"
UNTOUCHED_STATUS = 0
PROTECTED_COLOR = "#00FFFF"
PROTECTED_STATUS = 1
RISK_COLOR = "#FFFF00"
RISK_STATUS = 2
BURNING_COLOR = "#FF0000"
BURNING_STATUS = 3

logger = logging.getLogger('hsp-ff-brute')
ff_file = open(dir_path + '/output/brute_ff.txt', 'w')


def get_firefigthers_list(graph, burn_seq):
    out = []
    for i in range(len(burn_seq)):
        j = burn_seq[i]
        neigb1 = ()
        for n in j:
            neigb1 = set(neigb1.union(set(graph.neighbors(int(n)))))
        out.append([neigb1])
    return out


def run_firefigthers_against_fire_path(g, burn_seq, burn_seq_i, protect, neigb, budget, budget_h, budget_i, budget_j, out=[]):
    if len(burn_seq) == 0 and len(out) == 0: raise('nothing to protect!')

    if burn_seq_i in (0,1):
        run_firefigthers_against_fire_path(g, burn_seq, burn_seq_i+1, protect, neigb, budget, budget_h, budget_i, budget_j, out)
    else:
        #remove cells blocked by previous iteration

        #last step
        if burn_seq_i == len(burn_seq)-1:
            out.append(protect)
        #fire does not spread further
        elif set(burn_seq[burn_seq_i]).intersection(set(burn_seq[burn_seq_i-1])) == \
                set(burn_seq[burn_seq_i]):
            out.append(protect)
        #can protect all
        elif budget_i > len(burn_seq[burn_seq_i]):
            protect = protect + [protect[len(protect) - 1] + burn_seq[burn_seq_i]]
            out.append(protect)
        else:
            budget_h = budget_j
            budget_i = round(budget + budget_h, 2)
            budget_i_floor = round(math.floor(budget_i), 2)
            budget_j = round(budget_i - budget_i_floor, 2)
            comb = list(itertools.combinations(neigb, budget_i_floor))
            for i in comb:
                protect1 = protect + [protect[len(protect) - 1] + list(i)]
                neigb1 = set()
                lastBs = set(burning[len(burning) - 1] + list(i))  # burning[len(burning) - 1]
                for j in i:
                    neigb1 = neigb1.union(neigb.difference(i)).union(set(g.neighbors(int(j))).difference(lastBs))
                print(':: possibilities = ', comb, 'neig = ', neigb1)

                run_firefigthers_against_fire_path(g, burning1, neigb1, prop, out)

def gen_burning_list(output_file, graph, burning, neigb, prop, out=[]):
    if len(burning) == 0 and len(out) == 0: raise('nothing on fire!')

    if len(neigb) < prop:
        if len(neigb) == 0:
            #print(Bs)
            out.append(burning)
            output_file.write(str(burning)+'\n')
        else:
            out.append([[burning], [neigb]])
            #out.append(Bs[len(Bs)-1]+list(Bn))
            #print(Bs+[Bs[len(Bs)-1]+list(Bn)])
            output_file.write(str(burning)+'\n')
    else:
        # combinations for next iteration candidates
        comb = list(itertools.combinations(neigb, prop))
        for i in comb:
            burning1 = burning+[burning[len(burning)-1]+list(i)]
            neigb1 = set()
            lastBs = set(burning[len(burning)-1]+list(i)) #burning[len(burning) - 1]
            for j in i:
                neigb1 = neigb1.union(neigb.difference(i)).union(set(graph.neighbors(int(j))).difference(lastBs))
                #neigb1.extend(graph.neighbors(int(j)))
                #neigb1 = neigb1.union(neigb.difference(i)).union(set(graph.get(str(j), [])))
            print(':: possibilities = ', comb, 'neig = ', neigb1)

            gen_burning_list(output_file, graph, burning1, neigb1, prop, out)

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

def print_state(i, b, r, p, b_bef, bud_tot, but_tot_floor, b_aft):
    logger.debug('---------------------')
    logger.debug('iteration = ' + str(i))
    logger.debug('budget left (i-1) = {0:.2f}'.format(b_bef))
    logger.debug('budget current tot = {0:.2f}'.format(bud_tot))
    logger.debug('budget current (round) = {0:.2f}'.format(but_tot_floor))
    logger.debug('budget left (i+1) = {0:.2f}'.format(b_aft))
    logger.debug('burning = ' + str(len(b.queue)))
    logger.debug('in risk = ' + str(len(r.queue)))
    logger.debug('protected = ' + str(len(p.queue)))
    logger.debug('burning = ' + str([z for z in b.queue]))
    logger.debug('in risk = ' + str([z for z in r.queue]))
    logger.debug('protected = ' + str([z for z in p.queue]))

def simulate(n, g, budget, burns, B_cells, folder_sim):
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

    budget_bef = 0.0
    budget_i_tot = budget + budget_bef
    budget_i_floor = math.floor(budget_i_tot)
    budget_after = budget_i_tot - budget_i_floor

    print_state(0, q_burning, q_risk, q_protected, budget_bef, budget_i_tot, budget_i_floor, budget_after)

    # plot state 0
    plot(g, **visual_style, target=folder_sim  + 'out0.png')

    if q_risk.empty() is True:
        raise Exception('this should not occur')
    for i in range(budget_i_floor):
        i = q_risk.get()
        g.vs[i]["color"] = PROTECTED_COLOR
        g.vs[i]["status"] = PROTECTED_STATUS
        q_protected.put(i)

    print_state(1, q_burning, q_risk, q_protected, budget_bef, budget_i_tot, budget_i_floor, budget_after)

    iter = 1
    # plot state 1
    plot(g, **visual_style, target=folder_sim + 'out1.png')

    while not q_risk.empty():
        # burns and update risks
        iter += 1

        budget_bef = budget_after
        budget_i_tot = budget + budget_bef
        budget_i_floor = math.floor(budget_i_tot)
        budget_after = budget_i_tot - budget_i_floor

        if burns == -1:
            r = len(q_risk.queue)
        else:
            r = burns - 1

        temp_new_risk = queue.Queue()
        for i in range(r):
            irisk = q_risk.get()
            g.vs[irisk]["color"] = BURNING_COLOR
            g.vs[irisk]["status"] = BURNING_STATUS
            q_burning.put(irisk)
            temp_new_risk.put(irisk)

        while not temp_new_risk.empty():
            for i_new_risks in g.neighbors(temp_new_risk.get()):
                if g.vs[i_new_risks]["status"] == UNTOUCHED_STATUS:
                    g.vs[i_new_risks]["color"] = RISK_COLOR
                    g.vs[i_new_risks]["status"] = RISK_STATUS
                    q_risk.put(i_new_risks)
        # protect
        for i in range(budget_i_floor):
            if not q_risk.empty():
                irisk = q_risk.get()
                g.vs[irisk]["color"] = PROTECTED_COLOR
                g.vs[irisk]["status"] = PROTECTED_STATUS
                q_protected.put(irisk)

        print_state(iter, q_burning, q_risk, q_protected, budget_bef, budget_i_tot, budget_i_floor, budget_after)
        plot(g, **visual_style, target=folder_sim + 'out' + str(iter) + '.png')


    tot_untouched = len(list(v for v in g.vs["status"] if (v == UNTOUCHED_STATUS)))
    print_report(n, len(g.vs), iter, q_burning, q_risk, q_protected, budget, tot_untouched)

def brute_get_routes(exp_id, g, Bs, Bn, propagation):
    routes = []
    brute_file = open(dir_path + '/output/' + exp_id + '/' + exp_id + '.brute.fire', 'w')
    gen_burning_list(brute_file, g, Bs, Bn, propagation, routes)
    brute_file.close()
    return routes

def main(argv):

    # simulation parameters
    vertices = 3
    g = Graph.Lattice([vertices,vertices], nei=1, directed=False, mutual=True, circular=False)
    #g = Graph()
    #g.add_vertices(7)
    #g.add_edges([(0, 1), (0, 2), (0, 3), (0, 5)])
    #g.add_edges([(1, 4), (2, 5), (2, 6)])

    g.layout_grid(0, 0, dim=2)
    ga = g.get_adjlist()
    budget = 1.4
    burns = 2 # if burns = -1, then burns all neighbors of v_i at each iteration i, otherwise burns n neighbors
    Bs = list()
    Bs.append([0])
    Bn = []
    for v in Bs: Bn.extend(g.neighbors(v[0]))

    # simulation ID
    exp_id = get_sim_id(vertices, budget, burns, len(Bs))
    folder_sim = get_temp_folder(exp_id) + '/'

    #g = {
    #    '1': ['2', '3', '4', '5'],
    #    '2': ['6'],
    #    #'3': ['6', '7'],
    #}
    #Bs = list()
    #Bs.append([1])
    #Bn = set(g.get(str(1), []))

    # get the possible fire routes for brute force

    fire_routes = brute_get_routes(exp_id, g, Bs, set(Bn), burns)
    print('nr. simulations: ', fire_routes)
    exit(0)
    fire_sim_id = 0
    for fire_chain in fire_routes:
        ff_file = open(dir_path + '/output/' + exp_id + '/' + exp_id + '.brute.' + fire_sim_id + '.ff', 'w')
        ff = get_firefigthers_list(g, fire_chain, 0, [], [], budget, 0.0, 0.0, 0.0)
        ff_file.writelines(ff)
        ff_file.close()
        fire_sim_id+=1

    print('')
    exit(0)
    print('-|-')
    print(len(fire_routes))
    print(fire_routes)
    exit(0)



    # logging
    hdlr = logging.FileHandler(folder_sim + 'brute.log', mode='w')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)

    simulate(vertices, g, budget, burns, Bs, folder_sim)

    save_simulation(exp_id, folder_sim, burns)

if __name__ == "__main__":
    main(sys.argv[1:])