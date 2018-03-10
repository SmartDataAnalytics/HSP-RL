import itertools
import numpy as np
import random
import sys
'''
0 - unburned
1 - burned but still has neighbours
2 - all neighbours burned as well
3 - blocked by firefighter
'''
'''
spread order: randomized ;)
'''
class fireSimulation():
    
    fire = np.ndarray(shape=(4,4), dtype=float)
    
    fire_speed = 0

    time = 0


    def __init__(self,speed):
        self.fire_speed = speed
        self.fire.fill(0)
        #intialize the first spot
        #self.fire[random.randint(0,3)][random.randint(0,3)] = 1        
        self.fire[1][1] = 1
    def checkFire(self,fire):
        return (1 in fire.reshape(16))


    def checkNeighbour(self,x,y,fire):
        if (x>0 and (fire[x-1][y] == 1 or fire[x-1][y] == 2)) or x == 0:
            if (x<3 and (fire[x+1][y] == 1 or fire[x+1][y] == 2)) or x == 3:
                if (y>0 and (fire[x][y-1] == 1 or fire[x][y-1] == 2)) or y == 0:
                    if (y<3 and (fire[x][y+1] == 1 or fire[x][y+1] == 2)) or y == 3:
                        fire[x][y] = 2
        return fire


    # Fire spread functions
    def left(self,x,y,fire):
        if x>0 and fire[x-1][y] == 0:
            fire[x-1][y] = 1
            #fire = self.checkNeighbour(x-1,y,fire)
        return fire

    def right(self,x,y,fire):
        if x<3 and fire[x+1][y] == 0:
            fire[x+1][y] = 1
            #fire = self.checkNeighbour(x+1,y,fire)
        return fire

    def up(self,x,y,fire):
        if y>0 and fire[x][y-1] == 0:
            fire[x][y-1] = 1
            #fire = self.checkNeighbour(x,y-1,fire)
        return fire

    def down(self,x,y,fire):
        if y<3 and fire[x][y+1] == 0:
            fire[x][y+1] = 1
            #fire = self.checkNeighbour(x,y+1,fire)
        return fire




    def spread(self,x,y,fire):
        for i in range(self.fire_speed):
            #rnd = random.randint(0,3)
            rnd = i
            if rnd == 0:
                fire = self.left(x,y,fire)
            elif rnd == 1:
                fire = self.right(x,y,fire)
            elif rnd == 2:
                fire = self.up(x,y,fire)
            else:
                fire = self.down(x,y,fire)
        #fire = self.checkNeighbour(x,y,fire)
        return fire

    def iterFire(self,fire):
        #print(fire)
        firepoint = random.choice(self.findIndex(1,fire))
        x = firepoint[0]
        y = firepoint[1]
        fire = self.spread(x,y,fire)
        
        

    def _renderFire(self,fire):
        for x in range(4):
            print()
            for y in range(4):
                if fire[x][y] == 1:
                    sys.stdout.write('F')
                elif fire[x][y] == 0:
                    sys.stdout.write('0')
                elif fire[x][y] == 3:
                    sys.stdout.write('B')
                else:
                    sys.stdout.write('X')
            

    def findIndex(self,x,fire):
        returnlist = []
        for i in range(4):
            for j in range(4):
                if fire[i][j]==x:
                    returnlist.append([i,j])
        return returnlist


