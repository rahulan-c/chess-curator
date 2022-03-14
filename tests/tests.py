import time
import unittest
import chess
import chess.pgn

import utils
from helpers import check_if_move_is_uniquely_nonlosing, \
    check_position_against_masters_db



class SacDetectionTestCase(unittest.TestCase):

    def test_trapped_piece(self):

        cases = [
            # https://lichess.org/4z9FA9dC#21
            ["rn1qkb1r/1Q3ppp/p7/3ppb2/N2PnB2/4P3/PP3PPP/2R1KBNR b Kkq - 0 11",
                  "exf4", "Qxa8", True]
        ]

        for case in cases:
            board = chess.Board()
            board.set_fen(case[0])
            board.push_san(case[1])
            board.push_san(case[2])
            line = chess.pgn.Game()
            root = line.from_board(board)
            for node in root.mainline():
                if type(node.parent) is chess.pgn.ChildNode:
                    if case[3]:
                        self.assertTrue(utils.trapped_piece(node))
                    else:
                        self.assertFalse(utils.trapped_piece(node))


    def test_abs_pinned_piece(self):

        cases = [
            # https://lichess.org/IXeW8ATa#84
            ["8/2r2pp1/4p3/2Pnk3/7R/8/P3b1P1/4R1K1 b - - 2 42",
                  "Rxc5", "Rxe2", True],

            # https://lichess.org/hYJCjfqW#94
            ["8/6k1/6p1/1p3pr1/6N1/6K1/5P1P/1R6 w - - 0 47",
                  "Rxb5", "Rxg4", True],

            # https://lichess.org/m3kTTqR6#61
            ["R2b2k1/5pp1/2r4p/2Pp4/3PbB2/4P1P1/5P1P/6K1 b - - 1 30",
                  "Kh7", "Rxd8", True],

            # https://lichess.org/8fuYZcyt#35 (deliberate false case)
            ["r2r2k1/pp3pbp/1np3p1/q3Pb2/P2P1B2/5NP1/2Q2PBP/1R1R2K1 w - - 1 18",
                  "Qb3", "Bxb1", False]
        ]

        for case in cases:
            board = chess.Board()
            board.set_fen(case[0])
            board.push_san(case[1])
            board.push_san(case[2])
            line = chess.pgn.Game()
            root = line.from_board(board)
            for node in root.mainline():
                if type(node.parent) is chess.pgn.ChildNode:
                    if case[3]:
                        self.assertTrue(utils.captured_piece_was_abs_pinned(
                            node))
                    else:
                        self.assertFalse(utils.captured_piece_was_abs_pinned(
                            node))


    def test_skewer(self):

        cases = [
            # https://lichess.org/2WcWpKfH#20
            ["r2qkb1r/p3nppp/1pp1p3/3pP3/2b5/3Q1NP1/PP3PBP/RNB2RK1 w kq - 0 11",
                  "Qe3", "Bxf1", True],

            # https://lichess.org/8fuYZcyt#35
            ["r2r2k1/pp3pbp/1np3p1/q3Pb2/P2P1B2/5NP1/2Q2PBP/1R1R2K1 w - - 1 18",
                     "Qb3", "Bxb1", True],

            # FAILING CASES - NEED TO INVESTIGATE/FIX
            # https://lichess.org/dOC4d4at#45
            ["3q1rk1/1p3ppp/p2rp3/8/3b1PP1/BP3R2/P5KP/2R1Q3 b - - 1 23",
                  "Bb6", "Bxd6", False],

            # https://lichess.org/HC3JkhAZ#35
            ["1r1q2k1/3b1pp1/p1p2n1p/b1ppr3/P7/1P1P2BP/2PNNPP1/R2Q1RK1 b - - 1 18",
                  "Bc7", "Bxe5", False]
        ]

        for case in cases:
           # print(cases.index(case))
            board = chess.Board()
            board.set_fen(case[0])
            board.push_san(case[1])
            board.push_san(case[2])
            line = chess.pgn.Game()
            root = line.from_board(board)
            for node in root.mainline():
                # print(cases.index(case), node.san())
                if type(node.parent) is chess.pgn.ChildNode:
                    if case[3]:
                        self.assertTrue(utils.skewer(node))
                    else:
                        self.assertFalse(utils.skewer(node))

    def test_check_if_move_is_uniquely_nonlosing(self):
        self.assertTrue(check_if_move_is_uniquely_nonlosing(
            fen="5r1k/Bp2r1pp/4Q3/7q/1b6/8/PP2RPPP/R5K1 w - - 1 25",
            played="e6e7",
            engine_path="C:/Users/rahul/PycharmProjects/chess-curator/engine" \
                 "/stockfish_22031308_x64_avx2/stockfish_22031308_x64_avx2.exe"
        )
        )

    def test_check_move_against_masters_db(self):
        self.assertEquals(7, check_position_against_masters_db(
            fen = "rn2k2r/pp2bpp1/2p1pn1p/2Pp1b2/1P1P4/2N2NP1/1P2PPBP/R1B1K2R b KQkq - 0 10"))
        time.sleep(5)
        self.assertEquals(5, check_position_against_masters_db(
            fen="2bqr1k1/rpp2ppp/p1np1n2/4p3/4P3/1BPP1N2/PP1N1PPP/R2Q1RK1 w - - 0 11"))




if __name__ == '__main__':
    unittest.main()
