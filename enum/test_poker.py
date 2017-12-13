from poker import *
import unittest

class TestPokerHands(unittest.TestCase):
    '''
        PlayingCard (Enum)
        PlayingCardRank (Enum)
        PokerHand - validity, ranks and comparison of poker hands 
    '''
        
    def test_size_of_deck(self):
        self.assertEqual(len(list(PlayingCard)), 52)    
        
    def test_get_card_from_rank_and_suit(self):
        self.assertEqual(PlayingCard.get_card(Rank.NINE, Suit.SPADES),
                    PlayingCard.NINE_OF_SPADES)    

    def test_invalid_card_count(self):
        self.assertRaises(ValueError,
                          PokerHand,
                          [PlayingCard.ACE_OF_SPADES, 
                            PlayingCard.JACK_OF_SPADES, 
                            PlayingCard.ACE_OF_CLUBS, 
                            PlayingCard.TWO_OF_DIAMONDS,
                            PlayingCard.NINE_OF_DIAMONDS, 
                            PlayingCard.ACE_OF_HEARTS])

    def test_invalid_card_type(self):
        self.assertRaises(TypeError,
                          PokerHand,
                          [PlayingCard.ACE_OF_SPADES, 
                            PlayingCard.JACK_OF_SPADES, 
                            PlayingCard.ACE_OF_CLUBS, 
                            Suit.CLUBS,                  #not a card 
                            PlayingCard.ACE_OF_HEARTS])

    def test_nonunique_cards(self):
        self.assertRaises(ValueError,
                          PokerHand,
                          [PlayingCard.ACE_OF_SPADES, 
                            PlayingCard.ACE_OF_CLUBS, 
                            PlayingCard.ACE_OF_CLUBS,
                            PlayingCard.NINE_OF_DIAMONDS, 
                            PlayingCard.ACE_OF_HEARTS])

    def test_straight_flush(self):
        hand = PokerHand([PlayingCard.ACE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.QUEEN_OF_SPADES,PlayingCard.TEN_OF_SPADES, 
                          PlayingCard.KING_OF_SPADES])
        self.assertEqual(hand.hand_rank, PokerHandRank.STRAIGHT_FLUSH)
        
    def test_straight(self):
        hand = PokerHand([PlayingCard.NINE_OF_HEARTS, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.QUEEN_OF_CLUBS,PlayingCard.TEN_OF_SPADES, 
                          PlayingCard.KING_OF_SPADES])
        self.assertEqual(hand.hand_rank, PokerHandRank.STRAIGHT)
                          
    def test_flush(self):
        hand = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.FIVE_OF_SPADES,PlayingCard.TEN_OF_SPADES, 
                          PlayingCard.KING_OF_SPADES])
        self.assertEqual(hand.hand_rank, PokerHandRank.FLUSH)
        
    def test_4_KIND(self):
        hand = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.THREE_OF_CLUBS,PlayingCard.THREE_OF_HEARTS, 
                          PlayingCard.THREE_OF_DIAMONDS])
        self.assertEqual(hand.hand_rank, PokerHandRank.FOUR_OF_A_KIND)

    def test_3_KIND(self):
        hand = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.THREE_OF_CLUBS,PlayingCard.THREE_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        self.assertEqual(hand.hand_rank, PokerHandRank.THREE_OF_A_KIND)

    def test_FULL_HOUSE(self):
        hand = PokerHand([PlayingCard.FOUR_OF_SPADES, PlayingCard.TWO_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.FOUR_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        self.assertEqual(hand.hand_rank, PokerHandRank.FULL_HOUSE)

    def test_TWO_PAIR(self):
        hand = PokerHand([PlayingCard.NINE_OF_SPADES, PlayingCard.SIX_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.FOUR_OF_HEARTS, 
                          PlayingCard.SIX_OF_DIAMONDS])
        self.assertEqual(hand.hand_rank, PokerHandRank.TWO_PAIR)

    def test_PAIR(self):
        hand = PokerHand([PlayingCard.NINE_OF_SPADES, PlayingCard.SIX_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.FOUR_OF_HEARTS, 
                          PlayingCard.SEVEN_OF_DIAMONDS])
        self.assertEqual(hand.hand_rank, PokerHandRank.PAIR)

    def test_HIGH_CARD(self):
        hand = PokerHand([PlayingCard.NINE_OF_SPADES, PlayingCard.SIX_OF_SPADES,
                          PlayingCard.EIGHT_OF_CLUBS,PlayingCard.FOUR_OF_HEARTS, 
                          PlayingCard.SEVEN_OF_DIAMONDS])
        self.assertEqual(hand.hand_rank, PokerHandRank.HIGH_CARD)

    #comparisons : "beats"
    def test_FULL_HOUSE_beats_3_KIND(self):
        h1 = PokerHand([PlayingCard.FOUR_OF_SPADES, PlayingCard.TWO_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.FOUR_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        h2 = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.THREE_OF_CLUBS,PlayingCard.THREE_OF_HEARTS, 
                          PlayingCard.TWO_OF_HEARTS])
        self.assertTrue(h1 > h2)

    def test_TWO_PAIR_beats_PAIR(self):
        h1 = PokerHand([PlayingCard.FOUR_OF_SPADES, PlayingCard.TWO_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.SIX_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        h2 = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.THREE_OF_CLUBS,PlayingCard.NINE_OF_HEARTS, 
                          PlayingCard.KING_OF_HEARTS])
        self.assertTrue(h1 > h2)

    def test_FULL_HOUSE_beats_FULL_HOUSE(self):
        h1 = PokerHand([PlayingCard.FOUR_OF_SPADES, PlayingCard.TWO_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.FOUR_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        h2 = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.THREE_OF_CLUBS,PlayingCard.THREE_OF_HEARTS, 
                          PlayingCard.JACK_OF_HEARTS])
        self.assertTrue(h1 > h2)

    def test_TWO_PAIR_beats_TWO_PAIR(self):
        h1 = PokerHand([PlayingCard.FOUR_OF_SPADES, PlayingCard.TWO_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.SIX_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        h2 = PokerHand([PlayingCard.THREE_OF_SPADES, PlayingCard.JACK_OF_SPADES,
                          PlayingCard.THREE_OF_CLUBS,PlayingCard.NINE_OF_HEARTS, 
                          PlayingCard.JACK_OF_HEARTS])
        self.assertTrue(h2 > h1)

    def test_TWO_PAIR_beats_TWO_PAIR_same_ranks(self):
        h1 = PokerHand([PlayingCard.FOUR_OF_SPADES, PlayingCard.TWO_OF_SPADES,
                          PlayingCard.FOUR_OF_CLUBS,PlayingCard.SIX_OF_HEARTS, 
                          PlayingCard.TWO_OF_DIAMONDS])
        h2 = PokerHand([PlayingCard.FOUR_OF_DIAMONDS, PlayingCard.FOUR_OF_HEARTS,
                          PlayingCard.TWO_OF_CLUBS,PlayingCard.TWO_OF_HEARTS, 
                          PlayingCard.JACK_OF_HEARTS])
        self.assertTrue(h2 > h1)

if __name__ == '__main__':
    unittest.main()

  
