# elevator simulation with asyncio coroutines

import asyncio
import random
import time
from enum import Enum
Dir = Enum('Direction', 'UP DOWN STOPPED')
#ElAc = Enum('Elev Action', 'LOAD MOVE STEP UNLOAD')

class Dir(Enum):
    UP      = '↑' 
    DOWN    = '↓'
    STOPPED = '▪'


class FloorList:
    ''' i.e. the building state
        instead of a list of floor objects, 
        using lists of indexable attribute lists  ??? 
        besides not looking like traditional OOP,
        each floorcoro has access to whole list ??
    '''    
    def __init__(self, nfloors):
        self.nfloors = nfloors
        self.idents = [str(i + 1) for i in range(nfloors)]
        self.nupwaiting = {i : 0 for i in range(nfloors)} 
        self.ndownwaiting = {i : 0 for i in range(nfloors)} 
        
        #upreq[2] and downreq[0] will never be used 
        self.upreq = {i : False for i in range(nfloors)}
        self.downreq = {i : False for i in range(nfloors)}
                  
    def istop(self, floor):
        return floor == self.nfloors - 1
 
    def isbottom(self, floor):
        return floor == 0
        
    def add_upwaiting(self, ifloor, nriders):
        self.nupwaiting[ifloor] += nriders
        self.upreq[ifloor] = True

    def dec_upwaiting(self, ifloor, nriders):
        if nriders > self.nupwaiting[ifloor]:
            raise ValueError('decrementing upwaiting more than possible')
        self.nupwaiting[ifloor] -= nriders
        if self.nupwaiting[ifloor] == 0:
            self.upreq[ifloor] = False
        
    def add_downwaiting(self, ifloor, nriders):
        self.ndownwaiting[ifloor] += nriders
        self.downreq[ifloor] = True
            
    def dec_downwaiting(self, ifloor, nriders):
        if nriders > self.ndownwaiting[ifloor]:
            raise ValueError('decrementing downwaiting more than possible')
        self.ndownwaiting[ifloor] -= nriders
        if self.ndownwaiting[ifloor] == 0:
            self.downreq[ifloor] = False
           
    def random_floor(a, b):
        ''' pick random floor between a and b, where which is lower is uncertain'''
        pass       
    
async def floor_proc(floorlist, t_count):
    '''  accumulate riders '''
    ctr = 0
    await asyncio.sleep(2)
    
    while ctr < t_count:
        #dont add up for top nor down for bottom 
        floorlist.add_upwaiting(random.randint(0,floorlist.nfloors - 2), random.randint(1,2))
        floorlist.add_downwaiting(random.randint(1,2), random.randint(1,2))
                
        await asyncio.sleep(0.4)        
        ctr += random.randint(5, 10)

class Elevator:
    
    def __init__(self, ident, config):
        '''config is some structured text (json) with the particulars
           of the current building context: floors, action durations, etc'''
        self.ident = ident 
        self.maxriders = 10  #config.maxriders  
        self.nfloors = 3   # from config  ?? make this dynamic
        self.curdir = Dir.UP
        self.curfloor = 0
        self.nriders = 0
        self.reqs = { Dir.UP: [True, True, False], Dir.DOWN: [False, False, False] }
        # Dir.UP[nfloors - 1] and Dir.DOWN[0] will always be False
        # but it's convenient to keep the indexing consistent
        
        #print('new elev: ', self.ident)
        
    def __str__(self):
        return 'Elev {} at floor {} with {} riders, moving {} at {}'.format( \
               self.ident, self.curfloor, self.nriders, self.curdir, time.time())  
       
    def moved(self):
        ''' changes state, assumes direction has been adjusted for floor position '''
        if self.curdir == Dir.UP:
            self.curfloor += 1
        elif self.curdir == Dir.DOWN:
            self.curfloor -= 1

        if self.curfloor == self.nfloors - 1:   #at top
            self.curdir = Dir.DOWN
        elif self.curfloor == 0:
            self.curdir = Dir.UP 
            
    def hasrequest(self):
        if self.curdir == Dir.UP:
            return self.reqs[Dir.UP][self.curfloor]
        elif self.curdir == Dir.DOWN:
            return self.reqs[Dir.DOWN][self.curfloor]
        else:
            return False    #FIXME 
            
    def loadriders(self, floorlist, ctr):
        if floorlist.nupwaiting[self.curfloor] > 0 or floorlist.ndownwaiting[self.curfloor] > 0:
            print('loadable riders: {}, {}'.format(
                  floorlist.nupwaiting[self.curfloor], 
                  floorlist.ndownwaiting[self.curfloor])) 
        if self.curdir == Dir.UP:
            if floorlist.nupwaiting[self.curfloor] > 0:
                inc = min(self.maxriders - self.nriders, floorlist.nupwaiting[self.curfloor])
                self.nriders += inc 
                floorlist.dec_upwaiting(self.curfloor, inc)              
                ctr += random.randint(2, 5)  
            #get rider requests
            for rider in range(self.nriders):
                pick = random.randint(self.curfloor + 1, self.nfloors - 1)
                self.reqs[Dir.UP][pick] = True                        
        elif self.curdir == Dir.DOWN:
            if floorlist.ndownwaiting[self.curfloor] > 0:
                inc = min(self.maxriders - self.nriders, floorlist.ndownwaiting[self.curfloor])
                self.nriders += inc
                floorlist.dec_downwaiting(self.curfloor, inc)                
                ctr += random.randint(2, 5) 
            #get rider requests
            for rider in range(self.nriders):
                pick = random.randint(0, self.curfloor + 1)
                self.reqs[Dir.DOWN][pick] = True
            
            
    def makepanelrequest(self):
        ''' for each rider, pick a floor further along in the current direction '''
        pass
        
class ElevatorList:   
    '''singleton'''
    
    #config
    def __init__(self, count):
        self._elevs = []
        [self._elevs.append(Elevator('elev' + str(i + 1), None)) for i in range(count)]
        
    #def __iter__(self):
    #    return _elevs.__iter__()
        
    def __getitem__(self, i):
        return self._elevs[i]    
        
    def __len__(self):
        return len(_elevs) 
        
    def get_closest(floor):
        ''' used when assigning an elev to a requesting floor '''
        for e in elevs:
            pass                         
                
    
async def elev_proc(elev, floorlist, t_count):
    ''' TODO The floorlist's req's need to be assigned or claimed to an elev'''
    print(elev)
    
    ctr = 0
    await asyncio.sleep(2)
    
    #initial load;  otherwise only loads after a stop
    elev.loadriders(floorlist, ctr)
    
    while ctr < t_count:
        #get elev index from elev_ident, i.e. last char
        n = int(elev.ident[-1:]) - 1
        
        #move
        #due to async, the waiting rider counts shown here are not always up to date        
        print('{} moving {} with {} from f.{} at {}{} \t {},{}\t {},{}\t {},{} '.format(
               ' ' * (int(n > 0)) * 35, 
               elev.curdir.value, elev.nriders, floorlist.idents[elev.curfloor], ctr, 
               ' ' * (int(n == 0)) * 35,
               floorlist.nupwaiting[0], floorlist.ndownwaiting[0],
               floorlist.nupwaiting[1], floorlist.ndownwaiting[1],
               floorlist.nupwaiting[2], floorlist.ndownwaiting[2]))
        await asyncio.sleep(random.randint(1, 3) / 10)
        ctr += random.randint(5, 15)

        #stop at or pass floor
        elev.moved()
        if elev.hasrequest():
            print('{} now stopping at floor {} at {}'.format(' ' * n * 35, 
                   floorlist.idents[elev.curfloor], ctr))      
            await asyncio.sleep(random.randint(1, 4) / 10)
            ctr += random.randint(5, 10)

            #unload - these unloaded riders disappear from the sim
            if elev.nriders > 0:
                if floorlist.istop(elev.curfloor) or floorlist.isbottom(elev.curfloor):
                    elev.nriders = 0
                else:    
                    elev.nriders -= random.randint(0, elev.nriders)
                ctr += random.randint(2, 5)
                
            elev.loadriders(floorlist, ctr)
       
        else:
            ctr += 1
            print('{} passing floor {} at {}'.format(' ' * n * 35, 
                   floorlist.idents[elev.curfloor], ctr))
            await asyncio.sleep(0.01)
          
    return 'elev_proc {} done'.format(elev.ident) 
    

async def elev_controller(endtime):
    ''' takes requests and assigns each to an elevator as state      
    '''   
    print('started elevator controller')

    floorlist = FloorList(3)
    floor_coros = [floor_proc(floorlist, endtime) for i in range(3)]
    
    elevlist = ElevatorList(2)
    elev_coros = [elev_proc(elevlist[i], floorlist, endtime) for i in range(2)] 
    
         
    print('       elev.1                             elev.2                \tf.1\tf.2\tf.3')
    print('       ______                             ______                \t___\t___\t___')
    
    elev_res = await asyncio.gather(*elev_coros, *floor_coros)
    
    return elev_res


def main():
    ''' TODO:
             Config 
             Coordinate sim counters and await times'''
             
    t0 = time.time()
    event_loop = asyncio.get_event_loop()
    try:
        result = event_loop.run_until_complete(elev_controller(80))
        print('result: {!r}'.format(result))
    finally:
        event_loop.close()
    print("total time: ", str(time.time() - t0))    

if __name__ == "__main__":
    main()
    
'''
    
'''    
