import enum
from collections import Counter

class Suit(enum.Enum):
    SPADES   = (4, '♠')
    HEARTS   = (3, '♥')
    DIAMONDS = (2, '♦')
    CLUBS    = (1, '♣')


class Rank(enum.Enum):
    ACE   = (14, 'A')
    KING  = (13, 'K')
    QUEEN = (12, 'Q')
    JACK  = (11, 'J')
    TEN   = (10, '10')
    NINE  = (9,  '9')
    EIGHT = (8,  '8')
    SEVEN = (7,  '7')
    SIX   = (6,  '6')
    FIVE  = (5,  '5')
    FOUR  = (4,  '4')
    THREE = (3,  '3') 
    TWO   = (2,  '2') 

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] < other.value[0]
        return NotImplemented

    
class PlayingCardMeta(enum.EnumMeta):
    def __new__(metacls, cls, bases, classdict):
        for r in Rank:
            for s in Suit:                
                classdict[r.name + '_OF_' + s.name] = \
                    ((r.value[0] - 2) * 4 + s.value[0], r, s, r.value[1] + s.value[1])
            
        return super(PlayingCardMeta, metacls).__new__(metacls, cls, bases, classdict)

class PlayingCard(enum.Enum, metaclass=PlayingCardMeta):

    @property
    def rank(self):
        return self.value[1]
    
    @property    
    def suit(self):
        return self.value[2]
        
    @classmethod
    def get_card(self, rank, suit):
        return self.__dict__[rank.name + '_OF_' + suit.name]    
                   
    def __repr__(self): 
        return self.name

    def __str__(self): 
        return self.value[3]

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] >= other.value[0]
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] > other.value[0]
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] <= other.value[0]
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value[0] < other.value[0]
        return NotImplemented
                                

class PokerHandRank(enum.Enum):

    STRAIGHT_FLUSH   = 9
    FOUR_OF_A_KIND   = 8
    FULL_HOUSE       = 7
    FLUSH            = 6
    STRAIGHT         = 5
    THREE_OF_A_KIND  = 4
    TWO_PAIR         = 3
    PAIR             = 2
    HIGH_CARD        = 1
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
       
    @classmethod    
    def classify_hand(self, cards):
        ''' this implementation returns incomplete info
            for comparing hands 
            
            Parameter:  cards - list of 5 Playing cards 
                              - dont want to pass PokerHand to avoid circularity
                                or put this function in PokerHand class ???
            
            Returns:  tuple: handrank - a member instance of this class
                             high card - or high card in first group
                             second card - high card in second group  
            '''
        
        #test for Rank multiples
        ctr = Counter()        
        ctr.update([c.rank for c in cards])
        ctr_mc = ctr.most_common(5)
        
        high = PlayingCard.TWO_OF_CLUBS
        next_high = PlayingCard.TWO_OF_CLUBS # use None if this doesn't matter
        kicker = None # only used in the rare case of same TWO_PAIR using 5th card

        if ctr_mc[0][1] == 4:
            for c in cards:
                if c.rank == ctr_mc[0][0]:
                    if c > high:
                        high = c            
            return (self.FOUR_OF_A_KIND, high, None, None)
        elif ctr_mc[0][1] == 3:
            for c in cards:
                if c.rank == ctr_mc[0][0]:
                    if c > high:
                        high = c            
            if ctr_mc[1][1] == 2:
                #rank of triplet determines winner
                return (self.FULL_HOUSE, high, None, None)
            else:
                return (self.THREE_OF_A_KIND, high, None, None)
        elif ctr_mc[0][1] == 2:
            for c in cards:
                if c.rank == ctr_mc[0][0]:
                    if c > high:
                        high = c
                elif c.rank == ctr_mc[1][0]:
                    if c > next_high:
                        next_high = c                    
            if ctr_mc[1][1] == 2:
                for c in cards:
                    if c.rank != ctr_mc[0][0] and c.rank != ctr_mc[1][0]:
                        kicker = c
                # 2nd group may have higher rank than first, so reverse them
                if high.rank > next_high.rank:       
                    return (self.TWO_PAIR, high, next_high, kicker)
                else:
                    return (self.TWO_PAIR, next_high, high, kicker)                
            else:
                return (self.PAIR, high, next_high, None)        
        
        #otherwise mc_ctr counts are all `1`
        #test for flush, i.e. Suit multiples       
        is_flush = all([c.suit == cards[0].suit for c in cards[1:]])        
        is_straight = True  #temp
        
        #test for straight, sort by card.rank
        sorted_ranks = sorted(ctr.elements())

        for i in range(4):
            if sorted_ranks[i].value[0] != sorted_ranks[i + 1].value[0] - 1:
                is_straight = False
        
        for c in cards:
            if c > high:
                high = c
        
        if is_straight:
            if is_flush:
                return (self.STRAIGHT_FLUSH, high, None, None)
            else:
                return (self.STRAIGHT, high, None, None)
        
        if is_flush:
            return (self.FLUSH, high, None, None)
            
        #default is lowest rank
        return (self.HIGH_CARD, high, None, None)
        

class PokerHand():
    ''' instance of an ordered poker hand with containing a 
        list of 5 distinct PlayingCards
        ordering enables comparison between hands to establish a winner
        In matching hand ranks, the ranks are distinct and not subclassed,
        e.g. a STRAIGHT_FLUSH is not also a STRAIGHT  
    '''
    
    def __init__(self, cards):
        ''' cards must be a list of 5 distinct objects of Enum type 
            `PlayingCard` '''
    
        #validate cards
        if len(cards) != 5:
            raise ValueError('PokerHand Error: instance needs exactly 5 PlayingCard objects')
        elif not all(isinstance(c, PlayingCard) for c in cards):
            raise TypeError('PokerHand Error: instance needs parameter list of PlayingCard objects')
        elif len(cards) > len(set(cards)): 
            raise ValueError('Poker Hand Error: instance needs distinct cards')    
        else:
            self.cards = cards
            self.hand_rank, self.high, \
                self.next_high, self.kicker = PokerHandRank.classify_hand(cards)
                    
    def beats(self, other):
        if self.hand_rank > other.hand_rank:
            return True 
        elif other.hand_rank > self.hand_rank:
            return False
        else:
            if self.hand_rank in (PokerHandRank.FOUR_OF_A_KIND,
                                  PokerHandRank.FULL_HOUSE,
                                  PokerHandRank.THREE_OF_A_KIND,
                                  PokerHandRank.STRAIGHT_FLUSH,
                                  PokerHandRank.STRAIGHT,
                                  PokerHandRank.FLUSH,
                                  PokerHandRank.HIGH_CARD):
                return self.high > other.high 
            elif self.hand_rank == PokerHandRank.TWO_PAIR: 
                if self.high.rank > other.high.rank:
                    return True
                elif other.high.rank > self.high.rank:
                    return False
                elif self.next_high.rank > other.next_high.rank:
                        return True
                elif other.next_high.rank > self.next_high.rank:
                        return False
                else:  
                    return self.kicker > other.kicker               
            elif self.hand_rank == PokerHandRank.PAIR: 
                if self.high.rank > other.high.rank:
                    return True
                elif other.high.rank > self.high.rank:
                    return False
                else: 
                    return self.next_high > other.next_high               
    
    #hands are never equal
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.beats(other)  
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return not self.beats(other)
        return NotImplemented

