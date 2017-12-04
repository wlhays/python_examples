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


#ElAc = Enum('Elev Action', 'LOAD MOVE STEP UNLOAD')

class BDir(Enum):
    ''' Binary Direction, i.e. just two opposites 
        In the case of an unknown direction use the value `None`
        instead of a BDir.XXX value
        '''
    UP      = 'up' 
    DOWN    = 'down'

    def __str__(self):
        ''' shorthand for logging output '''
        if self is BDir.UP:
            return '↑'
        else:
            return '↓'


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
        ''' pick random floor between a and b, 
            where which one is lower is uncertain'''
        pass  
             
    
async def floor_proc(ifloor, floorlist, elevlist, t_count):
    '''  coroutine to accumulate riders and send stop requests to elevatorlist '''
    
    ncycles = 0
    
    while time.perf_counter() < t_count:  
        ncycles += 1
        
        #dont add up for top nor down for bottom 
        if not floorlist.istop(ifloor):
            inc_upw = random.randint(0,floorlist.nfloors)
            if inc_upw > 0:
                if not floorlist.upreq[ifloor]:
                    floorlist.upreq[ifloor] = True
                    elevlist.req_stop(ifloor, BDir.UP)
                floorlist.add_upwaiting(ifloor, inc_upw)
                    
        if not floorlist.isbottom(ifloor):
            inc_downw = random.randint(0,floorlist.nfloors)
            if inc_downw > 0:
                if not floorlist.downreq[ifloor]:
                    floorlist.downreq[ifloor] = True
                    elevlist.req_stop(ifloor, BDir.DOWN)
                floorlist.add_downwaiting(ifloor, inc_downw)
                          
        await asyncio.sleep(random.random())        

    print('floor_proc f.{} done with {} cycles'.format(ifloor + 1, ncycles))  
    return 'floor_proc f.{} done'.format(ifloor + 1, ncycles) 

class Elevator:
    
    def __init__(self, idx, elev_config):
        '''config is just the part for the particular elevator which is a dict'''
        self.idx = idx   
        self.ident = elev_config['name'] 
        self.maxriders = elev_config['maxriders']    
        self.nfloors = elev_config['floors_served']   
        self.curdir = BDir.UP
        self.curfloor = 0
        self.nriders = 0
        self.reqs = { BDir.UP: [False for i in range(self.nfloors)], 
                      BDir.DOWN: [False for i in range(self.nfloors)] }
        # BDir.UP[nfloors - 1] and BDir.DOWN[0] will always be False
        # but it's convenient to keep the indexing consistent
        
    def __str__(self):
        return 'Elev {} at f.{} with {} riders, moving {} at {:10.3f}'.format( \
               self.ident, self.curfloor, self.nriders, self.curdir, 
               time.perf_counter())  
       
    def moved(self):
        ''' changes elevator state to represent move to next floor '''
        if self.curdir == BDir.UP:
            self.curfloor += 1
        elif self.curdir == BDir.DOWN:
            self.curfloor -= 1

        if self.curfloor == self.nfloors - 1:   #at top
            self.curdir = BDir.DOWN
        elif self.curfloor == 0:
            self.curdir = BDir.UP 
    
    def hasanyrequest(self):
        return any(self.reqs[BDir.UP]) or any(self.reqs[BDir.DOWN])
            
    def hasrequest(self):
        if self.curdir == BDir.UP:
            return self.reqs[BDir.UP][self.curfloor]
        elif self.curdir == BDir.DOWN:
            return self.reqs[BDir.DOWN][self.curfloor]
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
        if self.curdir == BDir.UP:
            if floorlist.nupwaiting[self.curfloor] > 0:
                inc = min(self.maxriders - self.nriders, floorlist.nupwaiting[self.curfloor])
                self.nriders += inc 
                floorlist.dec_upwaiting(self.curfloor, inc)              
            #get rider requests
            for rider in range(self.nriders):
                pick = random.randint(self.curfloor + 1, self.nfloors - 1)
                self.reqs[BDir.UP][pick] = True                        
        elif self.curdir == BDir.DOWN:
            if floorlist.ndownwaiting[self.curfloor] > 0:
                inc = min(self.maxriders - self.nriders, floorlist.ndownwaiting[self.curfloor])
                self.nriders += inc
                floorlist.dec_downwaiting(self.curfloor, inc)                
            #get rider requests
            for rider in range(self.nriders):
                pick = random.randint(0, self.curfloor - 1)
                self.reqs[BDir.DOWN][pick] = True
                      
        
class ElevatorList:   
    '''singleton'''
    
    #config
    def __init__(self, config):
        self.elev_count = config['elevator_count']
        self.floor_count = config['floor_count']    
        self._elevs = []
        [self._elevs.append(Elevator(i, config['elevators'][i])) for i in range(self.elev_count)]
        
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
            if elev.curdir == BDir.UP:
                if reqfloor >= elev.curfloor:                    
                    dist = reqfloor - elev.curfloor
                else:   # below and behind
                    dist = max_dist - elev.curfloor + reqfloor 
            elif elev.curdir == BDir.DOWN:
                if reqfloor <= elev.curfloor:                    
                    dist = elev.curfloor - reqfloor
                else:   #above and behind
                    dist = max_dist - elev.curfloor + reqfloor 
        else:
            if elev.curdir == BDir.UP:
                dist = max_dist - elev.curfloor - reqfloor
            elif elev.curdir == BDir.DOWN:
                dist = elev.curfloor + reqfloor                
                
        return dist
                      
    
async def elev_proc(elev, floorlist, t_count):
    ''' coroutine for each elevator with a loop for each floor
        to floor move '''
    print(elev)
    
    #initial load;  otherwise only loads after a stop
    elev.loadriders(floorlist)
    
    while not elev.hasanyrequest():
        print("{}p-polling for req".format(' ' * elev.idx * 35))
        await asyncio.sleep(0.05)  # poll for request
        if time.perf_counter() >= t_count:
            break;
        
    ntrips = 0
    
    while time.perf_counter() < t_count:
        
        ntrips += 1
        nunloaded = 0
        
        #move
        #due to async, the waiting rider counts shown here are not always up to date        
        print('{} moving {!s} with {} from f.{} at {:5.3f}{} \t {},{}\t {},{}\t {},{} '.format(
               ' ' * (int(elev.idx > 0)) * 30, 
               elev.curdir, elev.nriders, floorlist.idents[elev.curfloor], 
               time.perf_counter(), 
               ' ' * (int(elev.idx == 0)) * 30,
               floorlist.nupwaiting[0], floorlist.ndownwaiting[0],
               floorlist.nupwaiting[1], floorlist.ndownwaiting[1],
               floorlist.nupwaiting[2], floorlist.ndownwaiting[2]))
 
        # poll for request
        while not elev.hasanyrequest() and elev.nriders == 0:
            print("{}polling for req".format(' ' * elev.idx * 35))
            await asyncio.sleep(0.2) 
            #need to check for endtime so doesn't hang  
            if time.perf_counter() >= t_count:
                break;

        #stop at or pass floor
        elev.moved()
        if elev.hasrequest() or floorlist.istop(elev.curfloor) or floorlist.isbottom(elev.curfloor):
            print('{} stopping at f.{} at {:5.3f}'.format(' ' * elev.idx * 35, 
                   floorlist.idents[elev.curfloor], 
                   time.perf_counter()))      
            await asyncio.sleep(random.randint(1, 4) / 10)

            #unload - these unloaded riders disappear from the sim
            if elev.nriders > 0:
                if floorlist.istop(elev.curfloor) or floorlist.isbottom(elev.curfloor):
                    nunloaded = elev.nriders
                    elev.nriders = 0
                else: 
                    nunloaded = random.randint(0, elev.nriders)   
                    elev.nriders -= nunloaded
                print('{} unloaded {} riders '.format( 
                       ' ' * (int(elev.idx > 0)) * 35,
                       nunloaded))   
            #load    
            elev.loadriders(floorlist)
       
        else:
            print('{} passing floor {} at {:5.3f}'.format(' ' * elev.idx * 35, 
                   floorlist.idents[elev.curfloor], 
                   time.perf_counter()))
            await asyncio.sleep(0.01)
            
    print('{}{} done with {} trips'.format(' ' * elev.idx * 35, elev.ident, ntrips))      
    return 'elev_proc {} done with {} trips'.format(elev.ident, ntrips) 
    

async def elev_controller(starttime, config):
    ''' takes requests and assigns each to an elevator as state      
    '''   
    print('started elevator controller')
    
    endtime = starttime + config['running_time']

    floorlist = FloorList(config['floor_count'])
    elevlist = ElevatorList(config)
    
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
             summary stats: trip and cycle durations, rider counts, etc.
             replace top(n) with gettop()
             replace hasreq() with hasreq(fl,dir)  ??
             review event duration times used in asyncio.sleep
             reassess access to config by various (moving) parts
             '''
     
    #TODO this can raise exeption if value not present
    print('total simulation time to run: ', config['running_time'])
             
    t0 = time.perf_counter()   #time()
    print('start time: {:3.4f}'.format(t0))  
    
    event_loop = asyncio.get_event_loop()
    try:
        result = event_loop.run_until_complete(elev_controller(t0, config))
        print('\nresult: {!r}'.format(result))
        #[print(i) for i in result]
    finally:
        event_loop.close()
    print('total time: {:3.4f}'.format(time.perf_counter() - t0))  #  time() - t0))    

DEFAULT_CONFIG = \
'''
---
#default elevsim config.yml
version : 0.2

running_time : 1.2
floor_count : 3
elevator_count : 2
elevator_maxriders : 10

elevators:
  - name : elev.1
    floors_served : 3 
    maxriders : 10
    loc :  west
    
  - name : elev.2
    floors_served : 3
    maxriders : 10
    loc:  east       
'''    

if __name__ == "__main__":
    if len(argv) == 2:
        try:
            with open(argv[1]) as f_config:
                config = yaml.safe_load(f_config)
                main(config)
        except OSError as e:  
            print(e)      
    else:    
        main(yaml.load(DEFAULT_CONFIG))
 
