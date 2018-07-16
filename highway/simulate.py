import time
import random
import shelve
import sys
import pdb

import cellular
reload(cellular)
#import qlearn_mod_random as qlearn # to use the alternative exploration method
import qlearn # to use standard exploration method
reload(qlearn)

directions = 4

lookdist = 2
lookcells = []
for i in range(-lookdist, lookdist+1):
    for j in range(-lookdist, lookdist+1):
        if (abs(i) + abs(j) <= lookdist) and (i != 0 or j != 0):
            lookcells.append((i, j))

def getTotalBurningCells():
    b=0
    for w in world.width:
        for h in world.height:
            cell = world.getCell(w, h)
            if cell.on_fire: b+=1
    return b

def pickRandomLocation():
    while 1:
        x = random.randrange(world.width)
        y = random.randrange(world.height)
        cell = world.getCell(x, y)
        if not (cell.wall or len(cell.agents) > 0):
            return cell


def catch_fire_neighbours():
    return 1


def distance_fire_to_highway():

    closest_burning_x, closest_burning_y = world.getClosestFire()
    highway_y = world.getHighway()
    return highway_y - closest_burning_y


class Cell(cellular.Cell):
    wall = False
    highway = False
    ff_blocked = False
    on_fire = False

    def colour(self):
        if self.wall:
            return 'black'
        elif self.highway:
            return 'blue'
        elif self.ff_blocked:
            return 'grey'
        elif self.on_fire:
            return 'red'
        else:
            return 'white'

    def load(self, data):
        if data == 'X':
            self.wall = True
        elif data == 'H':
            self.highway = True
        elif data == 'B':
            self.ff_blocked = True
        elif data == 'F':
            self.on_fire = True
        else:
            self.wall = False
            self.highway = False
            self.ff_blocked = False
            self.on_fire = False

'''
class Fire(cellular.Agent):
    cell = None
    score = 0
    colour = 'red'

    def update(self):
        cell = self.cell
        if cell != fire.cell:
            self.goTowards(fire.cell)
            while cell == self.cell:
                self.goInDirection(random.randrange(directions))


class FF_Dummy(cellular.Agent):
    cell = None
    score = 0
    colour = 'yellow'

    def update(self):
        cell = self.cell
        if cell != fire.cell:
            self.goTowards(fire.cell)
            while cell == self.cell:
                self.goInDirection(random.randrange(directions))
'''


class Fire(cellular.Agent):
    colour = 'orange'

    def __init__(self):
        self.tot_highway = 0
        self.tot_enclosed = 0
        self.tot_burning_cells = 1  # considering we always start with one burning cell, need to change later
        self.external_layer_on_fire = []

    def update(self):
        cell = self.cell
        _bc, _highway, _enclosed, _new_external_layer = \
            self.goSpread(fire.tot_burning_cells, fire.external_layer_on_fire)

        if _enclosed:
            self.tot_enclosed += 1
        if _highway:
            self.tot_highway += 1
        self.tot_burning_cells += _bc
        fire.external_layer_on_fire = _new_external_layer


class Firefighter(cellular.Agent):
    colour = 'gray'

    def __init__(self):
        self.ai = None
        self.ai = qlearn.QLearn(actions=range(directions), alpha=0.1, gamma=0.9, epsilon=0.1)
        self.lastState = None
        self.lastAction = None

    def update(self):
        # calculate the state of the surrounding cells
        state = self.calcState()
        # asign a reward of -1 by default
        reward = -1

        if world.highway_on_fire is True or fire.tot_burning_cells == world.tot_burning_cells:
            if world.highway_on_fire is True:
                self.highway_on_fire += 1
                reward = -100
            elif fire.tot_burning_cells == world.total_burning_cells:
                self.fire_enclosed += 1
                reward = 50

            if self.lastState is not None:
                self.ai.learn(self.lastState, self.lastAction, reward, state)
            self.lastState = None
            self.cell = pickRandomLocation()
            ff.cell = pickRandomLocation()
            return

        # Choose a new action and execute it
        state = self.calcState()
        print(state)
        action = self.ai.chooseAction(state)
        self.lastState = state
        self.lastAction = action
        self.goInDirection(action)

    def calcState(self):
        def cellvalue(cell):
            if cell.wall:
                return 1
            elif cell.ff_blocked:
                return 2
            elif cell.on_fire:
                return 3
            elif cell.highway:
                return 4
            else:
                return 0

        return tuple([cellvalue(self.world.getWrappedCell(self.cell.x + j, self.cell.y + i))
                      for i,j in lookcells])


ff = Firefighter()
fire = Fire()

world = cellular.World(Cell, directions=directions, filename='../worlds/ff_highway.txt')
world.age = 0

world.addAgent(ff, cell=pickRandomLocation())
world.addAgent(fire, cell=pickRandomLocation())

epsilonx = (0, 100000)
epsilony = (0.1, 0)
epsilonm = (epsilony[1] - epsilony[0]) / (epsilonx[1] - epsilonx[0])

endAge = world.age + 10000

world.display.activate(size=30)
world.display.delay = 1

# some initial learning
while world.age < endAge:
    world.update(fire.tot_burning_cells, fire.tot_enclosed)

    if world.age % 100 == 0:
        '''ff.ai.epsilon = (epsilony[0] if world.age < epsilonx[0] else
                                    epsilony[1] if world.age > epsilonx[1] else
                                    epsilonm*(world.age - epsilonx[0]) + epsilony[0])'''

        print "{:d}, e: {:0.2f}, W: {:d}, L: {:d}" \
            .format(world.age, ff.ai.epsilon, ff.highway_on_fire, ff.fire_enclosed)
        # ff.highway_on_fire = 0
        # ff.fire_enclosed = 0

print(ff.ai.q)

exit(0)

while 1:
    world.update(fire.tot_burning_cells, fire.highway, ff.fire_enclosed)
    print len(ff.ai.q)  # print the amount of state/action, reward elements stored
    bytes = sys.getsizeof(ff.ai.q)
    print "Bytes: {:d} ({:d} KB)".format(bytes, bytes / 1024)