import numpy as np
import sys
from gym.envs.toy_text import discrete

UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

class GridworldEnv(discrete.DiscreteEnv):


    metadata = {'render.modes': ['human', 'ansi']}

    def is_done(self, fire):
        for i in fire.reshape(16):
            if i == 1 or i == 2:
                return False
        return True

    def __init__(self, shape=[4,4]):
        if not isinstance(shape, (list, tuple)) or not len(shape) == 2:
            raise ValueError('shape argument must be a list/tuple of length 2')

        self.shape = shape

        nS = np.prod(shape)
        nA = 4

        MAX_Y = shape[0]
        MAX_X = shape[1]

        P = {}
        grid = np.arange(nS).reshape(shape)
        it = np.nditer(grid, flags=['multi_index'])

        # Initial state distribution is uniform
        isd = np.ones(nS) / nS

        super(GridworldEnv, self).__init__(nS, nA, P, isd)


    def changeP(self,fire,time):

        shape  = [4,4]

        nS = np.prod(shape)
        nA = 4

        MAX_Y = shape[0]
        MAX_X = shape[1]

        P = {}  #Policy
        grid = np.arange(nS).reshape(shape)
        it = np.nditer(grid, flags=['multi_index'])

        while not it.finished:
            s = it.iterindex
            y, x = it.multi_index


            P[s] = {a : [] for a in range(nS)}
            
            temp1 = np.where(fire.reshape(np.prod(shape)) == 1)
            temp2 = np.where(fire.reshape(np.prod(shape)) == 2)
        
#            is_done = lambda s: s == 0 or s == 15
#            is_done = lambda s: s in temp1[0] or s in temp2[0]
            reward = 0.0 if self.is_done(fire) else -1*time

            # We're stuck in a terminal state
            if self.is_done(fire):
                for i in range(16):
                    P[s][i] = [(1.0,s,reward,True)]
#                P[s][UP] = [(1.0, s, reward, True)]
#                P[s][RIGHT] = [(1.0, s, reward, True)]
#                P[s][DOWN] = [(1.0, s, reward, True)]
#                P[s][LEFT] = [(1.0, s, reward, True)]
            # Not a terminal state
            else:
#                fire = fire.reshape(16)
#                fire[s] = 3
#                fire = fire.reshape([4,4])
#                ns_up = s if y == 0 else s - MAX_X
#                ns_right = s if x == (MAX_X - 1) else s + 1
#                ns_down = s if y == (MAX_Y - 1) else s + MAX_X
#                ns_left = s if x == 0 else s - 1
                for i in range(16):
                    P[s][i] = [(1.0,i,reward, self.is_done(fire))]
#                P[s][UP] = [(1.0, ns_up, reward, is_done(ns_up))]
#                P[s][RIGHT] = [(1.0, ns_right, reward, is_done(ns_right))]
#                P[s][DOWN] = [(1.0, ns_down, reward, is_done(ns_down))]
#                P[s][LEFT] = [(1.0, ns_left, reward, is_done(ns_left))]

            it.iternext()

        super(GridworldEnv, self).update_P(P)
        return fire



    def _render(self,fire, mode='human', close=False):
        if close:
            return

        outfile = StringIO() if mode == 'ansi' else sys.stdout

        grid = np.arange(self.nS).reshape(self.shape)
        it = np.nditer(grid, flags=['multi_index'])
        while not it.finished:
            s = it.iterindex
            y, x = it.multi_index

            temp1 = np.where(fire.reshape(np.prod(4*4)) == 1)
            temp2 = np.where(fire.reshape(np.prod(4*4)) == 2)


            if self.s == s:
                output = " x "
            elif s in temp1[0] or s in temp2[0] :
                output = " T "
            else:
                output = " o "

            if x == 0:
                output = output.lstrip() 
            if x == self.shape[1] - 1:
                output = output.rstrip()

            outfile.write(output)

            if x == self.shape[1] - 1:
                outfile.write("\n")

            it.iternext()
