import random
import sys

import highway
from highway.simulate import *
from copy import copy, deepcopy

neighbourSynonyms = ('neighbours', 'neighbors', 'neighbour', 'neighbor')


class Cell:
    def __getattr__(self, key):
        if key in neighbourSynonyms:
            pts = [self.world.getPointInDirection(
                self.x, self.y, dir) for dir in range(self.world.directions)]
            ns = tuple([self.world.grid[y][x] for (x, y) in pts])
            for n in neighbourSynonyms:
                self.__dict__[n] = ns
            return ns
        raise AttributeError(key)

    #def update(self):
    #    from highway.simulate import Firefighter
    #    current_status = self._status
    #
    #    if len(self.agents) > 0:
    #
    #        if isinstance(self.agents[0], Firefighter):
    #            self._status = CELL_PROTECTED

class Agent:
    def __setattr__(self, key, val):
        if key == 'cell':
            old = self.__dict__.get(key, None)
            if old is not None:
                old.agents.remove(self)
            if val is not None:
                val.agents.append(self)
        self.__dict__[key] = val

    def __getattr__(self, key):
        if key == 'leftCell':
            return self.getCellOnLeft()
        elif key == 'rightCell':
            return self.getCellOnRight()
        elif key == 'aheadCell':
            return self.getCellAhead()
        raise AttributeError(key)

    def turn(self, amount):
        self.dir = (self.dir + amount) % self.world.directions

    def turnLeft(self):
        self.turn(-1)

    def turnRight(self):
        self.turn(1)

    def turnAround(self):
        self.turn(self.world.directions // 2)

    # return True if successfully moved in that direction
    def goInDirection(self, dir):
        target = self.cell.neighbour[dir]
        if target._status == CELL_WALL:
            return False, None, None, None, None
        else:
            last_status = copy(target._status)
            old_status = target._status
            target._status = CELL_PROTECTED
            self.cell = target
            return True, last_status, target.x, target.y, old_status

    def goForward(self):
        self.goInDirection(self.dir)

    def goBackward(self):
        self.turnAround()
        self.goForward()
        self.turnAround()

    def getCellAhead(self):
        return self.cell.neighbour[self.dir]

    def getCellOnLeft(self):
        return self.cell.neighbour[(self.dir - 1) % self.world.directions]

    def getCellOnRight(self):
        return self.cell.neighbour[(self.dir + 1) % self.world.directions]

    def goTowards(self, target):
        if self.cell == target:
            return
        best = None
        for n in self.cell.neighbours:
            if n == target:
                best = target
                break
            dist = (n.x - target.x) ** 2 + (n.y - target.y) ** 2
            if best is None or bestDist > dist:
                best = n
                bestDist = dist
        if best is not None:
            if getattr(best, 'wall', False):
                return
            self.cell = best

    def goSpread(self, tot_burning_i, external_layer_fire=[]):
        tot_bc = 0
        highway_hit = False
        enclosed = True
        temp = []
        updated_external_layer_fire = []

        for cell in external_layer_fire:
            for n in cell.neighbours:
                #n.check_consistency()
                if highway_hit is False and n._status == CELL_HIGHWAY:
                    highway_hit = True
                    print('attention! highway_hit!')
                if n._status == CELL_FREE:
                    n._status = CELL_BURNING
                    updated_external_layer_fire.append(n)
                    tot_bc += 1
                    enclosed = False

        tot_n_on_fire = tot_burning_i + tot_bc
        return tot_n_on_fire, highway_hit, enclosed, updated_external_layer_fire


class World:
    def __init__(self, cell=None, width=None, height=None, directions=8, filename=None):
        if cell is None:
            cell = Cell
        self.Cell = cell
        self.display = makeDisplay(self)
        self.directions = directions
        if filename is not None:
            data = open(filename).readlines()
            if height is None:
                height = len(data)
            if width is None:
                width = max([len(x.rstrip()) for x in data])
        if width is None:
            width = 20
        if height is None:
            height = 20
        self.width = width
        self.height = height
        self.image = None

        # fire fighter - highway problem
        self.is_highway_on_fire = False
        self.is_fire_enclosed = False

        self.score_fire = None
        self.score_enclosed = None

        self.tot_burning_cells = 0
        self.tot_free_cells = 0
        self.tot_highway_cells_protected = 0 # TODO: implement this logic
        self.highway_meta_coordinates = None

        self.highway_min_x = 999999999
        self.highway_max_x = 0
        self.highway_min_y = 999999999
        self.highway_max_y = 0

        self.reset()
        if filename is not None:
            self.load(filename)

    def set_tot_free_cells(self):
        tot = 0
        for w in range(self.width):
            for h in range(self.height):
                cell = self.getCell(w, h)
                if cell._status == CELL_FREE:
                    tot+=1
        self.tot_free_cells = tot


    def print_world_status_cells(self):
        counts = {CELL_FREE: 0, CELL_HIGHWAY: 0, CELL_WALL: 0, CELL_PROTECTED: 0, CELL_BURNING: 0}
        out=''
        for w in range(self.width):
            for h in range(self.height):
                cell = self.getCell(w, h)
                counts[cell._status] = counts.get(cell._status) + 1
        for k, v in counts.items():
            out += ind2labels.get(k) + ': ' + str(v) + ' '
        print(out)

    def set_highway_meta_coordinates(self, coordinates):
        self.highway_meta_coordinates = coordinates

    def getCell(self, x, y):
        return self.grid[y][x]

    def getWrappedCell(self, x, y):
        return self.grid[y % self.height][x % self.width]

    def reset(self):
        self.grid = [[self.makeCell(
            i, j) for i in range(self.width)] for j in range(self.height)]
        self.dictBackup = [[{} for i in range(self.width)]
                           for j in range(self.height)]
        self.agents = []
        self.age = 0

    def makeCell(self, x, y):
        c = self.Cell()
        c.x = x
        c.y = y
        c.world = self
        c.agents = []
        return c

    def randomize(self):
        if not hasattr(self.Cell, 'randomize'):
            return
        for row in self.grid:
            for cell in row:
                cell.randomize()

    def save(self, f=None):
        if not hasattr(self.Cell, 'save'):
            return
        if isinstance(f, type('')):
            f = open(f, 'w')

        total = ''
        for j in range(self.height):
            line = ''
            for i in range(self.width):
                line += self.grid[j][i].save()
            total += '%s\n' % line
        if f is not None:
            f.write(total)
            f.close()
        else:
            return total

    def load(self, f):
        if not hasattr(self.Cell, 'load'):
            return
        if isinstance(f, type('')):
            f = open(f)
        lines = f.readlines()
        lines = [x.rstrip() for x in lines]
        fh = len(lines)
        fw = max([len(x) for x in lines])
        if fh > self.height:
            fh = self.height
            starty = 0
        else:
            starty = (self.height - fh) // 2
        if fw > self.width:
            fw = self.width
            startx = 0
        else:
            startx = (self.width - fw) // 2

        self.reset()
        for j in range(fh):
            line = lines[j]
            for i in range(min(fw, len(line))):
                self.grid[starty + j][startx + i].load(line[i])

    def update(self, fire=0, enclosed=0):
        if hasattr(self.Cell, 'update'):
            for j, row in enumerate(self.grid):
                for i, c in enumerate(row):
                    self.dictBackup[j][i].update(c.__dict__)
                    c.update()
                    c.__dict__, self.dictBackup[j][
                        i] = self.dictBackup[j][i], c.__dict__
            for j, row in enumerate(self.grid):
                for i, c in enumerate(row):
                    c.__dict__, self.dictBackup[j][
                        i] = self.dictBackup[j][i], c.__dict__
            for a in self.agents:
                a.update()
            self.display.redraw()
        else:
            for a in self.agents:
                oldCell = a.cell
                a.update()
                if oldCell != a.cell:
                    self.display.redrawCell(oldCell.x, oldCell.y)
                self.display.redrawCell(a.cell.x, a.cell.y)

        self.score_fire = fire
        self.score_enclosed = enclosed

        self.display.redraw() #AQUI
        self.display.update()
        self.age += 1

    def getPointInDirection(self, x, y, dir):
        if self.directions == 8:
            dx, dy = [(0, -1), (1, -1), (
                1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)][dir]
        elif self.directions == 4:
            dx, dy = [(0, -1), (1, 0), (0, 1), (-1, 0)][dir]
        elif self.directions == 6:
            if y % 2 == 0:
                dx, dy = [(1, 0), (0, 1), (-1, 1), (-1, 0),
                          (-1, -1), (0, -1)][dir]
            else:
                dx, dy = [(1, 0), (1, 1), (0, 1), (-1, 0),
                          (0, -1), (1, -1)][dir]

        x2 = x + dx
        y2 = y + dy

        if x2 < 0:
            x2 += self.width
        if y2 < 0:
            y2 += self.height
        if x2 >= self.width:
            x2 -= self.width
        if y2 >= self.height:
            y2 -= self.height

        return (x2, y2)

    def addAgent(self, agent, x=None, y=None, cell=None, dir=None):
        self.agents.append(agent)
        if cell is not None:
            x = cell.x
            y = cell.y
        if x is None:
            x = random.randrange(self.width)
        if y is None:
            y = random.randrange(self.height)
        if dir is None:
            dir = random.randrange(self.directions)
        agent.cell = self.grid[y][x]
        agent.dir = dir
        agent.world = self


import time


def makeDisplay(world):
    d = Display()
    d.world = world
    return d


class DummyDisplay:
    def activate(self, size=4):
        pass

    def redraw(self):
        pass

    def redrawCell(self, x, y):
        pass

    def update(self):
        pass

    def setTitle(self, title):
        pass


class TkinterDisplay:
    activated = False
    paused = False
    title = ''
    updateEvery = 1
    root = None
    delay = 0

    def activate(self, size=4):
        self.bg = None
        self.size = size
        if TkinterDisplay.root is None:
            TkinterDisplay.root = Tkinter.Tk()
        for c in self.root.winfo_children():
            c.destroy()
        self.activated = True
        self.imageLabel = Tkinter.Label(self.root)
        self.imageLabel.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=1)
        self.frameWidth, self.frameHeight = self.world.width * \
            size, self.world.height * size
        self.root.geometry(
            '%dx%d' % (self.world.width * size, self.world.height * size))
        self.root.update()
        self.redraw()
        self.root.bind('<Configure>', self.onConfigure)
        self.root.bind('<Prior>', self.onPageUp)
        self.root.bind('<Next>', self.onPageDown)
        self.root.bind('<space>', self.pause)
        self.root.bind('<Escape>', self.quit)

    def quit(self, event):
        self.root.destroy()

    def update(self):
        if not self.activated:
            return
        if self.world.age % self.updateEvery != 0 and not self.paused:
            return
        self.setTitle(self.title)
        self.imageLabel.update()
        if self.delay > 0:
            time.sleep(self.delay * 0.1)

    def setTitle(self, title):
        if not self.activated:
            return
        self.title = title
        title += ' %s' % makeTitle(self.world)
        if self.root.title() != title:
            self.root.title(title)

    def onConfigure(self, event):
        if event.width != self.frameWidth or event.height != self.frameHeight:
            oldSize = self.size
            scalew = event.width // self.world.width
            scaleh = event.height // self.world.height
            self.size = min(scalew, scaleh)
            if self.size < 1:
                self.size = 1
            if oldSize < self.size:
                self.imageCache.clear()
            if oldSize != self.size:
                self.redraw()
            self.frameWidth = event.width
            self.frameHeight = event.height

    def onPageDown(self, event):
        if self.updateEvery > 1:
            self.updateEvery //= 2
        else:
            self.delay += 1
        if self.delay > 10:
            self.delay = 10

    def onPageUp(self, event):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.updateEvery *= 2

    def pause(self, event=None):
        self.paused = not self.paused
        while self.paused:
            self.update()

    def getBackground(self):
        if self.bg is None:
            r, g, b = self.imageLabel.winfo_rgb(self.root['background'])
            self.bg = '%c%c%c' % (r >> 8, g >> 8, b >> 8)
        return self.bg

    def redraw(self):
        if not self.activated:
            return
        hexgrid = self.world.directions == 6

        iw = self.world.width * self.size
        ih = self.world.height * self.size
        if hexgrid:
            iw += self.size // 2

        f = open('temp.ppm', 'wb')
        f.write('P6\n%d %d\n255\n' % (iw, ih))

        odd = False
        for row in self.world.grid:
            line = cStringIO.StringIO()
            if hexgrid and odd:
                line.write(self.getBackground() * (self.size // 2))
            for cell in row:
                if len(cell.agents) > 0:
                    c = self.getDataColour(cell.agents[-1])
                else:
                    c = self.getDataColour(cell)

                line.write(c * self.size)
            if hexgrid and not odd:
                line.write(self.getBackground() * (self.size // 2))
            odd = not odd

            f.write(line.getvalue() * self.size)
        f.close()

        self.image = Tkinter.PhotoImage(file='temp.ppm')
        self.imageLabel.config(image=self.image)

    imageCache = {}

    def redrawCell(self, x, y):
        if not self.activated:
            return
        sx = x * self.size
        sy = y * self.size
        if y % 2 == 1 and self.world.directions == 6:
            sx += self.size // 2

        cell = self.world.grid[y][x]
        if len(cell.agents) > 0:
            c = self.getTextColour(cell.agents[-1])
        else:
            c = self.getTextColour(cell)

        sub = self.imageCache.get(c, None)
        if sub is None:
            sub = Tkinter.PhotoImage(width=1, height=1)
            sub.put(c, to=(0, 0))
            sub = sub.zoom(self.size)
            self.imageCache[c] = sub
        self.image.tk.call(self.image, 'copy', sub, '-from', 0, 0, self.size, self.size, '-to', sx, sy)

    def getTextColour(self, obj):
        c = getattr(obj, 'colour', None)
        if c is None:
            c = getattr(obj, 'color', 'white')
        if callable(c):
            c = c()
        if isinstance(c, type(())):
            if isinstance(c[0], type(0.0)):
                c = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
            return '#%02x%02x%02x' % c
        return c

    dataCache = {}

    def getDataColour(self, obj):
        c = getattr(obj, 'colour', None)
        if c is None:
            c = getattr(obj, 'color', 'white')
        if callable(c):
            c = c()
        if isinstance(c, type(())):
            if isinstance(c[0], type(0.0)):
                c = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
            return '%c%c%c' % c
        else:
            val = self.dataCache.get(c, None)
            if val is None:
                r, g, b = self.imageLabel.winfo_rgb(c)
                val = '%c%c%c' % (r >> 8, g >> 8, b >> 8)
                self.dataCache[c] = val
            return val


class PygameDisplay:
    activated = False
    paused = False
    title = ''
    updateEvery = 1
    delay = 0
    screen = None

    def activate(self, size=4):
        self.size = size
        pygame.init()
        w = self.world.width * size
        h = self.world.height * size
        if self.world.directions == 6:
            w += size // 2
        if PygameDisplay.screen is None or PygameDisplay.screen.get_width() != w or PygameDisplay.screen.get_height() != h:
            PygameDisplay.screen = pygame.display.set_mode(
                (w, h), pygame.RESIZABLE, 32)
        self.activated = True
        self.defaultColour = self.getColour(self.world.grid[0][0].__class__())
        self.redraw()

    def redraw(self):
        if not self.activated:
            return
        self.screen.fill(self.defaultColour)
        hexgrid = self.world.directions == 6
        self.offsety = (
            self.screen.get_height() - self.world.height * self.size) // 2
        self.offsetx = (
            self.screen.get_width() - self.world.width * self.size) // 2
        sy = self.offsety
        odd = False
        for row in self.world.grid:
            sx = self.offsetx
            if hexgrid and odd:
                sx += self.size // 2
            for cell in row:
                if len(cell.agents) > 0:
                    c = self.getColour(cell.agents[0])
                else:
                    c = self.getColour(cell)
                if c != self.defaultColour:
                    try:
                        self.screen.fill(c, (sx, sy, self.size, self.size))
                    except TypeError:
                        print('Error: invalid colour:', c)
                sx += self.size
            odd = not odd
            sy += self.size

    def redrawCell(self, x, y):
        if not self.activated:
            return
        sx = x * self.size + self.offsetx
        sy = y * self.size + self.offsety
        if y % 2 == 1 and self.world.directions == 6:
            sx += self.size // 2

        cell = self.world.grid[y][x]
        if len(cell.agents) > 0:
            c = self.getColour(cell.agents[0])
        else:
            c = self.getColour(cell)

        self.screen.fill(c, (sx, sy, self.size, self.size))

    def update(self):
        if not self.activated:
            return
        if self.world.age % self.updateEvery != 0 and not self.paused:
            return
        self.setTitle(self.title)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit()
            elif event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.onResize(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                if self.delay > 0:
                    self.delay -= 1
                else:
                    self.updateEvery *= 2
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                if self.updateEvery > 1:
                    self.updateEvery /= 2
                else:
                    self.delay += 1
                if self.delay > 10:
                    self.delay = 10
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.pause()

        pygame.display.flip()
        if self.delay > 0:
            time.sleep(self.delay * 0.1)

    def setTitle(self, title):
        if not self.activated:
            return
        self.title = title
        title += ' %s' % makeTitle(self.world)
        if pygame.display.get_caption()[0] != title:
            pygame.display.set_caption(title)

    def pause(self, event=None):
        self.paused = not self.paused
        while self.paused:
            self.update()

    def onResize(self, event):
        if not self.activated:
            return
        pygame.display.set_mode(event.size, pygame.RESIZABLE, 32)
        oldSize = self.size
        scalew = event.size[0] // self.world.width
        scaleh = event.size[1] // self.world.height
        self.size = min(scalew, scaleh)
        if self.size < 1:
            self.size = 1
        self.redraw()

    def getColour(self, obj):
        c = getattr(obj, 'colour', None)
        if c is None:
            c = getattr(obj, 'color', 'white')
        if callable(c):
            c = c()
        if isinstance(c, type(())):
            if isinstance(c[0], type(0.0)):
                c = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
            return c
        return pygame.color.Color(c)

    def saveImage(self, filename=None):
        if filename is None:
            filename = '%05d.bmp' % self.world.age
        pygame.image.save(self.screen, filename)


def makeTitle(world):
    text = 'age: %d' % world.age
    extra = []
    if world.score_enclosed:
        extra.append('fire_enclosed=%d' % world.score_enclosed)
    if world.score_fire:
        extra.append('highway_on_fire=%d' % world.score_fire)
    if world.display.paused:
        extra.append('paused')
    if world.display.updateEvery != 1:
        extra.append('skip=%d' % world.display.updateEvery)
    if world.display.delay > 0:
        extra.append('delay=%d' % world.display.delay)

    if len(extra) > 0:
        text += ' [%s]' % ', '.join(extra)
    return text

try:
    print('PygameDisplay')
    import pygame
    Display = PygameDisplay
except:
    try:
        print('Tkinter')
        import Tkinter
        import cStringIO
        Display = TkinterDisplay
    except:
        print('DummyDisplay')
        Display = DummyDisplay
