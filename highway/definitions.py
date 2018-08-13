CELL_FREE = 0
CELL_HIGHWAY = 1
CELL_WALL = 2
CELL_PROTECTED = 3
CELL_BURNING = 4

ind2labels = {CELL_FREE: 'free', CELL_HIGHWAY: 'highway', CELL_WALL: 'wall', CELL_PROTECTED: 'protected', CELL_BURNING: 'burning'}
labels2ind = {'free': CELL_FREE, 'highway': CELL_HIGHWAY, 'wall': CELL_WALL,
              'protected': CELL_PROTECTED, 'burning': CELL_BURNING}