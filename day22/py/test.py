import unittest
import main


class DealToStackTest(unittest.TestCase):
    def test_deal_to_stack(self):
        deck = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        res = main.deal_to_stack(deck)
        self.assertEqual(res, [9, 8, 7, 6, 5, 4, 3, 2, 1])

    def test_deal_to_empty_stack(self):
        deck = []
        res = main.deal_to_stack(deck)
        self.assertEqual([], res)


class CutDeckTest(unittest.TestCase):
    def test_cut_positive(self):
        deck = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        res = main.cut_n_cards(deck, 3)
        self.assertEqual(res, [4, 5, 6, 7, 8, 9, 1, 2, 3])

    def test_cut_negative(self):
        deck = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        res = main.cut_n_cards(deck, -4)
        self.assertEqual(res, [6, 7, 8, 9, 1, 2, 3, 4, 5])

    def test_cut_zero(self):
        deck = []
        res = main.cut_n_cards(deck, 0)
        self.assertEqual(res, [])

    def test_cut_exceeded_length(self):
        self.assertRaises(ValueError, main.cut_n_cards, [], 5)


class DealByNTest(unittest.TestCase):
    def test_deal_by_n(self):
        deck = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        res = main.deal_by_n(deck, 3)
        self.assertEqual(res, [0, 7, 4, 1, 8, 5, 2, 9, 6, 3])

    def test_deal_divisible(self):
        deck = [0, 1, 2, 3]
        self.assertRaises(ValueError, main.deal_by_n, deck, 2)

    def test_negative_n(self):
        deck = [0, 1, 2, 3]
        self.assertRaises(ValueError, main.deal_by_n, deck, -1)


class TestParsing(unittest.TestCase):
    def test_parse_deal_by_n(self):
        cmd = 'deal with increment 55'
        self.assertEqual((main.Operation.DEAL_BY_N, 55), main.parse_command(cmd))

    def test_parse_deal_to_stack(self):
        cmd = 'deal into new stack'
        self.assertEqual((main.Operation.DEAL_TO_STACK, None), main.parse_command(cmd))

    def test_parse_cut_n_cards(self):
        cmd = 'cut 55'
        self.assertEqual((main.Operation.CUT, 55), main.parse_command(cmd))

    def test_parse_cut_n_negative(self):
        cmd = 'cut -55'
        self.assertEqual((main.Operation.CUT, -55), main.parse_command(cmd))


if __name__ == '__main__':
    unittest.main()
