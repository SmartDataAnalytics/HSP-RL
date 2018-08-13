import time
import random
import shelve
import sys
import pdb
import numpy as np
from highway import cellular
from importlib import reload
#import cellular
from highway.definitions import *

reload(cellular)
#import qlearn_mod_random as qlearn # to use the alternative exploration method
from highway import qlearn # to use standard exploration method
reload(qlearn)

directions = 4

lookdist = 20
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
            if cell._status == CELL_BURNING: b+=1
    return b

def pickRandomLocation(which_half=None):
    while 1:
        x = random.randrange(world.width)
        if which_half == 1:
            y = random.randrange(0, world.height // 2)
        elif which_half == -1:
            y = random.randrange((world.height // 2) + 1, world.height)
        else:
            raise Exception('which_half value not valid')

        cell = world.getCell(x, y)
        if cell._status == CELL_FREE and not len(cell.agents) > 0:
            return cell


def catch_fire_neighbours():
    return 1


def distance_fire_to_highway():

    closest_burning_x, closest_burning_y = world.getClosestFire()
    highway_y = world.getHighway()
    return highway_y - closest_burning_y


def _get_highway_meta_coordinates():
    highway_coordinates = []
    for x in range(world.width):
        for y in range(world.height):
            cell = world.getCell(x, y)
            if cell._status == CELL_HIGHWAY:
                highway_coordinates.append('{}|{}'.format(x, y))
    assert len(highway_coordinates) > 0
    return highway_coordinates


def _revert_the_enviroment_status():
    for x in range(world.width):
        for y in range(world.height):
            c = world.getCell(x, y)
            metacoordinate = '{}|{}'.format(x, y)
            if metacoordinate in world.highway_meta_coordinates:
                c._status = CELL_HIGHWAY
            elif c._status not in (CELL_HIGHWAY, CELL_WALL):
                c._status = CELL_FREE


class Cell(cellular.Cell):
    _status = CELL_FREE

    '''
    def check_consistency(self):

        condition1 = self._free is True and (self._wall is False and self._highway is False and
                               self._protected is False and self._burning is False)

        condition2 = self._free is False and (self._wall is True or self._highway is True or
                                        self._protected is True or self._burning is True)

        values = [self._wall, self._highway, self._protected, self._burning]
        condition3 = len(np.count_nonzero([values], axis=0)) == 1

        print(condition1, condition2, condition3)
        assert condition1 or (condition2 and condition3)

   
    def set_free(self):

        if self._wall is True or self._highway is True:
            raise Exception('can not free a highway or wall!')

        self._free = True

        self._wall = False
        self._highway = False
        self._protected = False
        self._burning = False

    def set_protected(self):
        self._free = False
        self._protected = True

    def set_burning(self):
        self._free = False
        self._burning = True

    '''
    def colour(self):

        if self._status == CELL_WALL:
            return 'black'
        elif self._status == CELL_HIGHWAY:
            return 'gray'
        elif self._status == CELL_PROTECTED:
            return 'dark blue'
        elif self._status == CELL_BURNING:
            return 'dark red'
        elif self._status == CELL_FREE:
            return 'white'
        else:
            Exception('colour err')

    def load(self, data):

        if data == 'X':
            self._status = CELL_WALL
        elif data == 'H':
            self._status = CELL_HIGHWAY
        elif data == 'B':
            self._status = CELL_PROTECTED
        elif data == 'F':
            self._status = CELL_BURNING
        else:
            self._status = CELL_FREE

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


class Flame(cellular.Agent):
    colour = 'light coral'

    def __init__(self):
        self.tot_highway = 0
        self.tot_enclosed = 0
        self.tot_burning_cells = 1  # considering we always start with one burning cell, need to change later
        self.external_layer_on_fire = []

    def update(self):
        cell = self.cell

        #self.print_external_layer_on_fire()

        if len(self.external_layer_on_fire) == 0:
            layer = [cell]
        else:
            layer = self.external_layer_on_fire

        _bc, _highway_hit, _enclosed, _new_external_layer = self.goSpread(flame.tot_burning_cells, layer)

        # just keep the last layer catching fire
        self.external_layer_on_fire = _new_external_layer
        for c in self.external_layer_on_fire:
            wc = world.getCell(c.x, c.y)
            wc._status == CELL_BURNING
        world.tot_burning_cells = _bc

        if _enclosed:
            self.tot_enclosed += 1
        if _highway_hit:
            world.is_highway_on_fire = True
            self.tot_highway += 1
        self.tot_burning_cells = _bc

    def print_external_layer_on_fire(self):
        for c in self.external_layer_on_fire:
            print(c.x, c.y)

    def get_distance_to_highway(self):
        max_y = int(world.highway_meta_coordinates[0][0])
        max_y_fire = -1
        for c in self.external_layer_on_fire:
            if max_y_fire < c.y:
                max_y_fire = c.y
        return abs(max_y - max_y_fire)


class Firefighter(cellular.Agent):
    colour = 'light blue'

    def __init__(self):
        self.ai = None
        self.ai = qlearn.QLearn(actions=range(directions), alpha=0.1, gamma=0.9, epsilon=0.1)
        self.lastState = None
        self.lastAction = None

    def update(self):
        # calculate the state of the surrounding cells
        state = self.calcState()
        #print(state)

        # highway on fire or fire enclosed
        # -- end of game
        reward = -1
        if world.is_highway_on_fire or world.is_fire_enclosed:

            if world.is_highway_on_fire:
                reward = -100
            if world.is_fire_enclosed:
                reward = 100

            if self.lastState is not None:
                self.ai.learn(self.lastState, self.lastAction, reward, state)
            self.lastState = None

            world.is_highway_on_fire = False
            world.is_fire_enclosed = False
            self.cell = pickRandomLocation(1)
            flame.cell = pickRandomLocation(-1)
            flame.tot_burning_cells = 1
            flame.external_layer_on_fire = []

            # revert the cells status
            _revert_the_enviroment_status()

            return

        else:
            d = flame.get_distance_to_highway()
            b = flame.tot_burning_cells
            v = d * b
            reward = (np.log(abs(v)) * -1) * 10
            #print(reward)
            print(self.cell._status)

            if self.cell._status == CELL_HIGHWAY:
                reward = 200
            elif self.cell._status == CELL_FREE:
                reward = 10
            elif self.cell._status == CELL_PROTECTED:
                reward = -10
            #print(reward)

            s = ''
            '''
            
            if self.cell._status == CELL_PROTECTED:
                reward = -50
                s='protected'
            elif self.cell._status == CELL_HIGHWAY:
                reward = -100
                s='highway'
            elif self.cell._status == CELL_BURNING:
                reward = 25
                s='burning'
            elif self.cell._status == CELL_FREE:
                
                s='free'
            elif self.cell._status == CELL_WALL:
                s='well'    
            else:
                raise Exception('')
            '''


            #print(':: reward=%s :: external layer=%s :: type=%s' % (reward, len(flame.external_layer_on_fire),s))

            if self.lastState is not None:
                self.ai.learn(self.lastState, self.lastAction, reward, state)

            # Choose a new action and execute it
            state = self.calcState()
            #print(state)
            action = self.ai.chooseAction(state)
            self.lastState = state
            self.lastAction = action

            sucess, last_status, last_cell_x, last_cell_y = self.goInDirection(action)
            if sucess and last_status == CELL_BURNING:
                flame.tot_burning_cells -= 1
                # removes from last layer, in case it is there
                for i in range(len(flame.external_layer_on_fire)):
                    if flame.external_layer_on_fire[i].x == last_cell_x \
                            and flame.external_layer_on_fire[i].y == last_cell_y:
                        flame.external_layer_on_fire.pop(i)
                        break



    def calcState(self):
        def cellvalue(cell):
            return cell._status

        return tuple([cellvalue(self.world.getWrappedCell(self.cell.x + j, self.cell.y + i))
                      for i, j in lookcells])


flame = Flame()
ff = Firefighter()

world = cellular.World(Cell, directions=directions, filename='../worlds/ff_highway.txt')
world.age = 0

world.addAgent(flame, cell=pickRandomLocation(-1))
world.addAgent(ff, cell=pickRandomLocation(1))

epsilonx = (0, 100000)
epsilony = (0.1, 0)
epsilonm = (epsilony[1] - epsilony[0]) / (epsilonx[1] - epsilonx[0])

endAge = world.age + 10000

highway_X_Y = _get_highway_meta_coordinates()

world.set_highway_meta_coordinates(highway_X_Y)

world.display.activate(size=10)
world.display.delay = 0
world.print_world_status_cells()
# some initial learning
while world.age < endAge:
    #world.display.redraw()
    world.update(flame.tot_highway, flame.tot_enclosed)
    world.print_world_status_cells()

    '''
    if world.age % 100 == 0:
        ff.ai.epsilon = (epsilony[0] if world.age < epsilonx[0] else
                                    epsilony[1] if world.age > epsilonx[1] else
                                    epsilonm*(world.age - epsilonx[0]) + epsilony[0])

        print("{:d}, e: {:0.2f}, W: {:d}, L: {:d}".format(world.age, ff.ai.epsilon,
                                                          flame.tot_highway, flame.tot_enclosed))
        # ff.highway_on_fire = 0
        # ff.fire_enclosed = 0
    '''

print(ff.ai.q)

world.display.delay = 1
while 1:
    world.update(flame.tot_highway, flame.tot_enclosed)
    world.print_world_status_cells()
    #print(len(ff.ai.q))  # print the amount of state/action, reward elements stored
    #bytes = sys.getsizeof(ff.ai.q)
    #print("Bytes: {:d} ({:d} KB)".format(bytes, bytes / 1024))