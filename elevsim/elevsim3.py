# elevator simulation with asyncio coroutines
'''
20171201 - elev_procs poll for requests before moving

         - changed timing to just specify an end time and test each
           coro while loop, as opposed to accumulating bits of time


'''

import asyncio
import random
import time
import yaml
from enum import Enum
from sys import argv


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
      
    #not used TODO remove       
    def random_floor(a, b):
        ''' pick random floor between a and b, where which is lower is uncertain'''
        pass  
             
    
async def floor_proc(ifloor, floorlist, elevlist, t_count):
    '''  accumulate riders ; send stop requests to elevatorlist '''
  
    #await asyncio.sleep(0.02)
    
    ncycles = 0
    
    while time.perf_counter() < t_count:  
        ncycles += 1
        
        #dont add up for top nor down for bottom 
        if not floorlist.istop(ifloor):
            inc_upw = random.randint(0,3)
            if inc_upw > 0:
                if not floorlist.upreq[ifloor]:
                    floorlist.upreq[ifloor] = True
                    elevlist.req_stop(ifloor, Dir.UP)
                floorlist.add_upwaiting(ifloor, inc_upw)
                    
        if not floorlist.isbottom(ifloor):
            inc_downw = random.randint(0,3)
            if inc_downw > 0:
                if not floorlist.downreq[ifloor]:
                    floorlist.downreq[ifloor] = True
                    elevlist.req_stop(ifloor, Dir.DOWN)
                floorlist.add_downwaiting(ifloor, inc_downw)
                          
        await asyncio.sleep(random.random())        
        #ctr += random.randint(5, 10)

    print('floor_proc f.{} done with {} cycles'.format(ifloor + 1, ncycles))  
    return 'floor_proc f.{} done'.format(ifloor + 1, ncycles) 

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
        self.reqs = { Dir.UP: [False, False, False], Dir.DOWN: [False, False, False] }
        # Dir.UP[nfloors - 1] and Dir.DOWN[0] will always be False
        # but it's convenient to keep the indexing consistent
        
        #print('new elev: ', self.ident)
        
    def __str__(self):
        return 'Elev {} at f.{} with {} riders, moving {} at {:10.3f}'.format( \
               self.ident, self.curfloor, self.nriders, self.curdir, time.perf_counter())  
       
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
    
    def hasanyrequest(self):
        return any(self.reqs[Dir.UP]) or any(self.reqs[Dir.DOWN])
            
    def hasrequest(self):
        if self.curdir == Dir.UP:
            return self.reqs[Dir.UP][self.curfloor]
        elif self.curdir == Dir.DOWN:
            return self.reqs[Dir.DOWN][self.curfloor]
        else:
            return False 
            
    def loadriders(self, floorlist):
        #print("{}loading riders".format(' ' * 70))
        if floorlist.nupwaiting[self.curfloor] > 0 or floorlist.ndownwaiting[self.curfloor] > 0:
            print('{}waiting on f.{}: {}, {}'.format(
                  ' ' * 70, 
                  self.curfloor + 1, 
                  floorlist.nupwaiting[self.curfloor], 
                  floorlist.ndownwaiting[self.curfloor])) 
        if self.curdir == Dir.UP:
            if floorlist.nupwaiting[self.curfloor] > 0:
                inc = min(self.maxriders - self.nriders, floorlist.nupwaiting[self.curfloor])
                self.nriders += inc 
                floorlist.dec_upwaiting(self.curfloor, inc)              
                #ctr += random.randint(2, 5)  
            #get rider requests
            for rider in range(self.nriders):
                pick = random.randint(self.curfloor + 1, self.nfloors - 1)
                self.reqs[Dir.UP][pick] = True                        
        elif self.curdir == Dir.DOWN:
            if floorlist.ndownwaiting[self.curfloor] > 0:
                inc = min(self.maxriders - self.nriders, floorlist.ndownwaiting[self.curfloor])
                self.nriders += inc
                floorlist.dec_downwaiting(self.curfloor, inc)                
                #ctr += random.randint(2, 5) 
            #get rider requests
            for rider in range(self.nriders):
                pick = random.randint(0, self.curfloor - 1)
                self.reqs[Dir.DOWN][pick] = True
        #return ctr
                      
    #def makepanelrequest(self):
    #    ''' for each rider, pick a floor further along in the current direction '''
    #    pass
        
class ElevatorList:   
    '''singleton'''
    
    #config
    def __init__(self, elev_count, floor_count):
        self.elev_count = elev_count
        self.floor_count = floor_count
    
        self._elevs = []
        [self._elevs.append(Elevator('elev' + str(i + 1), None)) for i in range(elev_count)]
        
    #def __iter__(self):
    #    return _elevs.__iter__()
        
    def __getitem__(self, i):
        return self._elevs[i]    
        
    def __len__(self):
        return len(_elevs) 
        
    def req_stop(self, reqfloor, reqdir):
        '''assign to one elevator'''
        e = self._get_closest(reqfloor, reqdir)
        e.reqs[reqdir][reqfloor] = True 
        print('req for {} made for f.{}'.format(e.ident, reqfloor + 1))   
        
    def _get_closest(self, reqfloor, reqdir):
        ''' used when assigning an elev to a requesting floor
            return closest elev object
        '''
        
        closest = self._elevs[0]  #arbitrary 
        min_dist = (self.floor_count - 1) * 2 + 1
        max_dist = min_dist - 1
        
        for e in self._elevs:
            d = self._get_dist(e, reqfloor, reqdir, max_dist)
            if d < min_dist:
                min_dist = d
                closest = e
            elif d == min_dist:
                closest = random.choice([e, closest])

        print('{}req= f.{}{} c= {}, d= {}'.format(
               ' ' * 68, reqfloor + 1, reqdir.value, closest.ident, min_dist))        
        return closest                          
                
    def _get_dist(self, elev, reqfloor, reqdir, max_dist):
        '''calculate the distance between the elev and floor'''
        dist = max_dist
        
        if elev.curdir == reqdir:
            if elev.curdir == Dir.UP:
                if reqfloor >= elev.curfloor:                    
                    dist = reqfloor - elev.curfloor
                else:   # below and behind
                    dist = max_dist - elev.curfloor + reqfloor 
            elif elev.curdir == Dir.DOWN:
                if reqfloor <= elev.curfloor:                    
                    dist = elev.curfloor - reqfloor
                else:   #above and behind
                    dist = max_dist - elev.curfloor + reqfloor 
        else:
            if elev.curdir == Dir.UP:
                dist = max_dist - elev.curfloor - reqfloor
            elif elev.curdir == Dir.DOWN:
                dist = elev.curfloor + reqfloor                
        #print("calc dist: {}".format(dist))     #TODO remove
        return dist
                      
    
async def elev_proc(elev, floorlist, t_count):
    ''' coroutine for each elevator with a loop for each floor
        to floor move '''
    print(elev)
    
    n = int(elev.ident[-1:]) - 1
    
    #without this, one elev never goes anywhere ??
    #await asyncio.sleep(1)
    
    #initial load;  otherwise only loads after a stop
    elev.loadriders(floorlist)
    
    while not elev.hasanyrequest():
        print("{}p-polling for req".format(' ' * n * 35))
        await asyncio.sleep(0.05)  # poll for request
        if time.perf_counter() >= t_count:
            break;
        #ctr += 0.2
        
    #while ctr < t_count:
    ntrips = 0
    
    while time.perf_counter() < t_count:
        #get elev index from elev_ident, i.e. last char
        
        ntrips += 1
        nunloaded = 0
        
        #move
        #due to async, the waiting rider counts shown here are not always up to date        
        print('{} moving {} with {} from f.{} at {:5.3f}{} \t {},{}\t {},{}\t {},{} '.format(
               ' ' * (int(n > 0)) * 30, 
               elev.curdir.value, elev.nriders, floorlist.idents[elev.curfloor], 
               time.perf_counter(), 
               ' ' * (int(n == 0)) * 30,
               floorlist.nupwaiting[0], floorlist.ndownwaiting[0],
               floorlist.nupwaiting[1], floorlist.ndownwaiting[1],
               floorlist.nupwaiting[2], floorlist.ndownwaiting[2]))
 
        # poll for request
        while not elev.hasanyrequest() and elev.nriders == 0:
            print("{}polling for req".format(' ' * n * 35))
            await asyncio.sleep(0.2) 
            #need to check for endtime so doesn't hang  
            if time.perf_counter() >= t_count:
                break;

        #await asyncio.sleep(random.randint(1, 3) / 10)
        #ctr += random.randint(5, 15)

        #stop at or pass floor
        elev.moved()
        if elev.hasrequest() or floorlist.istop(elev.curfloor) or floorlist.isbottom(elev.curfloor):
            print('{} stopping at f.{} at {:5.3f}'.format(' ' * n * 35, 
                   floorlist.idents[elev.curfloor], 
                   time.perf_counter()))      
            await asyncio.sleep(random.randint(1, 4) / 10)
            #ctr += random.randint(5, 10)

            #unload - these unloaded riders disappear from the sim
            if elev.nriders > 0:
                if floorlist.istop(elev.curfloor) or floorlist.isbottom(elev.curfloor):
                    nunloaded = elev.nriders
                    elev.nriders = 0
                else: 
                    nunloaded = random.randint(0, elev.nriders)   
                    elev.nriders -= nunloaded
                print('{} unloaded {} riders '.format( 
                       ' ' * (int(n > 0)) * 35,
                       nunloaded))   
                #ctr += random.randint(2, 5)
            #load    
            elev.loadriders(floorlist)
       
        else:
            #ctr += 1
            print('{} passing floor {} at {:5.3f}'.format(' ' * n * 35, 
                   floorlist.idents[elev.curfloor], 
                   time.perf_counter()))
            await asyncio.sleep(0.01)
            
    print('{}{} done with {} trips'.format(' ' * n * 35, elev.ident, ntrips))      
    return 'elev_proc {} done with {} trips'.format(elev.ident, ntrips) 
    

async def elev_controller(endtime):
    ''' takes requests and assigns each to an elevator as state      
    '''   
    print('started elevator controller')

    floorlist = FloorList(3)
    elevlist = ElevatorList(2, 3) #TODO config with details ...
    
    floor_coros = [floor_proc(i, floorlist, elevlist, endtime) for i in range(3)]
    #TODO change signature to match above: i, elevlist, ...
    elev_coros = [elev_proc(elevlist[i], floorlist, endtime) for i in range(2)] 
             
    print('       elev.1                             elev.2                \tf.1\tf.2\tf.3')
    print('       ______                             ______                \t___\t___\t___')
    
    elev_res = await asyncio.gather(*elev_coros, *floor_coros)
    
    return elev_res


def main(config):
    ''' TODO:
             alternate way to wait for request, e.g. queue
             Config validation
             summary stats
             implement up/down as boolean? e.g. class Dir(Boolean, Enum) ?Hmmm, UP == not DOWN
             replace top(n) with gettop()
             replace hasreq() with hasreq(fl,dir)
             try block for opening config
             remove ctr in elev_proc
             in elevproc, n var needs better name or ?
             
             '''
     
    #TODO this can raise exeption if value not present
    print('total simulation time to run: ', config['running_time'])
             
    t0 = time.perf_counter()   #time()
    print('start time: {:3.4f}'.format(t0))     
    
    event_loop = asyncio.get_event_loop()
    try:
        result = event_loop.run_until_complete(elev_controller(t0 + config['running_time']))
        print('\nresult: {!r}'.format(result))
        #[print(i) for i in result]
    finally:
        event_loop.close()
    print('total time: {:3.4f}'.format(time.perf_counter() - t0))  #  time() - t0))    

DEFAULT_CONFIG = \
'''
---
#default elevsim config.yml
version : 0.1

running_time : 3
floor_count : 3
elevator_count : 2    
'''    

if __name__ == "__main__":
    if len(argv) == 2:
        #TODO try:
        with open(argv[1]) as f_config:
            config = yaml.safe_load(f_config)
            main(config)
    else:    
        main(yaml.load(DEFAULT_CONFIG))
 
