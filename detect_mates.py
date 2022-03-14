# ==================  DETECT CHECKMATES =======================================

# Detect checkmates given by a knight, bishop or pawn
# Detect back rank checkmates
# To add: more interesting checkmates

# USER OPTIONS
# Select source of games
# 1: Lichess game IDs
# 2: previously uploaded PGN file ('games.pgn')
games_source = 2

# Choose whether to sample games (and sample size)
sample_games = False
sample_size = 200

# =============================================================================

from rich import print
from tqdm import tqdm
from chess import square_rank, square_file, Board, SquareSet, Piece, PieceType, \
    square_distance
from chess import KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN
from chess import WHITE, BLACK, Outcome, Termination
from chess.pgn import ChildNode
from IPython.display import Image
from IPython.display import display
from IPython.display import HTML
import cairosvg
import chess.pgn
import random
import chess.svg
import io
import glob
import os
import pandas as pd
import shutil

import choices
import utils

# pgn_file = 'games.pgn'
pgn_file = 'games_team4545_s12.pgn'

# Read PGN
pgn = open(pgn_file)

offsets = []
mates = []

knight_mates = []
bishop_mates = []
pawn_mates = []
backrank_mates = []
anastasia_mates = []
hook_mates = []
arabian_mates = []
smothered_mates = []

knight_gameids = []
bishop_gameids = []
pawn_gameids = []
backrank_gameids = []
anastasia_gameids = []
hook_gameids = []
arabian_gameids = []
smothered_gameids = []

while True:

    # Scan PGN headers for faster parsing
    offset = pgn.tell()
    headers = chess.pgn.read_headers(pgn)

    if headers is None:
        break
    else:
        offsets.append(offset)

total_games = len(offsets)

# Get random sample of games
offsets = random.sample(offsets, sample_size) if sample_games else offsets

print('#####################################')
print("  IDENTIFY INTERESTING CHECKMATES  ")
print('#####################################')
print('')
print(f"Reading {pgn_file} ({len(offsets)} games)")
print('')

# Loop through each selected game
for offset in tqdm(offsets):

    pgn.seek(offset)
    game = chess.pgn.read_game(pgn)

    # Show all checkmates
    final = game.end().board()
    outcome = final.outcome()
    if outcome == None or not outcome.termination == Termination(1):
        continue

    mates.append(game.headers['Site'][-8:])

    # Get final position
    position = final.fen()

    # Identify the piece that delivered mate
    mate_piece = list(final.checkers())
    if len(mate_piece) is 1:
        mate_square = chess.Square(mate_piece[0])

        if final.piece_at(mate_square).symbol() in ('n', 'N'):
            knight_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                                size=250,
                                                coordinates=False))
            knight_gameids.append(game.headers['Site'][-8:])

        if final.piece_at(mate_square).symbol() in ('b', 'B'):
            bishop_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                                size=250,
                                                coordinates=False))
            bishop_gameids.append(game.headers['Site'][-8:])

        if final.piece_at(mate_square).symbol() in ('p', 'P'):
            pawn_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                              size=250,
                                              coordinates=False))
            pawn_gameids.append(game.headers['Site'][-8:])

    # Back-rank mate
    if back_rank_mate(game):
        backrank_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                              size=250,
                                              coordinates=False))
        backrank_gameids.append(game.headers['Site'][-8:])

    # Anastasia's mate
    if anastasia_mate(position):
        anastasia_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                               size=250,
                                               coordinates=False))
        anastasia_gameids.append(game.headers['Site'][-8:])

    # Hook mate
    if hook_mate(position):
        hook_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                          size=250,
                                          coordinates=False))
        hook_gameids.append(game.headers['Site'][-8:])

    # Arabian mate
    if arabian_mate(position):
        arabian_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                             size=250,
                                             coordinates=False))
        arabian_gameids.append(game.headers['Site'][-8:])

    # Smothered mates
    if smothered_mate(position):
        smothered_mates.append(chess.svg.board(final, lastmove=final.peek(),
                                               size=250,
                                               coordinates=False))
        smothered_gameids.append(game.headers['Site'][-8:])

# After checking all games...
print('')
print('==== RESULTS ====')
print('')
print(f"{len(mates)} games ended in checkmate")
print('')
print(f"{len(knight_mates)} games ended with mate delivered by a knight")
print(f"{len(bishop_mates)} games ended with mate delivered by a bishop")
print(f"{len(pawn_mates)} games ended with mate delivered by a pawn")
print('')
print(f"{len(backrank_mates)} games ended with a back rank mate")
print(f"{len(anastasia_mates)} games ended with an Anastasia's mate")
print(f"{len(hook_mates)} games ended with a hook mate")
print(f"{len(arabian_mates)} games ended with an Arabian mate")
print(f"{len(smothered_mates)} games ended with a smothered mate")
print('')

# First delete any previously saved PNGs
for pngpath in glob.iglob(os.path.join('*.png')):
    os.remove(pngpath)

# Then save PNGs of knight/bishop/pawn mates
for m in range(len(knight_mates)):
    cairosvg.svg2png(bytestring=knight_mates[m],
                     write_to=f"knight-mate-{m + 1:02}-{knight_gameids[m]}.png")

for m in range(len(bishop_mates)):
    cairosvg.svg2png(bytestring=bishop_mates[m],
                     write_to=f"bishop-mate-{m + 1:02}-{bishop_gameids[m]}.png")

for m in range(len(pawn_mates)):
    cairosvg.svg2png(bytestring=pawn_mates[m],
                     write_to=f"pawn-mate-{m + 1:02}-{pawn_gameids[m]}.png")

for m in range(len(backrank_mates)):
    cairosvg.svg2png(bytestring=backrank_mates[m],
                     write_to=f"backrank-mate-{m + 1:02}-{backrank_gameids[m]}.png")

for m in range(len(anastasia_mates)):
    cairosvg.svg2png(bytestring=anastasia_mates[m],
                     write_to=f"anastasia-mate-{m + 1:02}-{anastasia_gameids[m]}.png")

for m in range(len(hook_mates)):
    cairosvg.svg2png(bytestring=hook_mates[m],
                     write_to=f"hook-mate-{m + 1:02}-{hook_gameids[m]}.png")

for m in range(len(arabian_mates)):
    cairosvg.svg2png(bytestring=arabian_mates[m],
                     write_to=f"arabian-mate-{m + 1:02}-{arabian_gameids[m]}.png")

for m in range(len(smothered_mates)):
    cairosvg.svg2png(bytestring=smothered_mates[m],
                     write_to=f"smothered-mate-{m + 1:02}-{smothered_gameids[m]}.png")

# # Then display PNGs below
# images = glob.glob("*.png")
# images.sort()
# for i in range(len(images)):
#     display(str(i + 1) + ' / ' + str(len(images)),
#             Image(filename = images[i]),
#             '', '')







