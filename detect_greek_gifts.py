"""Identify "Greek Gift" sacrifices and assess their quality.

Motivated by a suggestion by https://lichess.org/@/AACtrl in the Lichess4545
Slack.
Objective: identify likely Greek gift sacs and assess their quality using
PGN eval data or a local engine.
Current version appears to identify mostly plausible sacs but only for White
and doesn't check sac quality.

TODO: expand to identify sacs by Black
TODO: add castling and king position logic
TODO: add engine checks
"""

import random

import chess
import pandas as pd
from chess.pgn import ChildNode
from tqdm import tqdm
from datetime import datetime

import choices
import helpers
from helpers import read_pgn

# Helpers and parameters
task_label = "GreekGifts"
now = datetime.now()
now_label = f"{now.year}{now.month}{now.day}_{now.hour}{now.minute}"

# Read PGN file
pgn = read_pgn(helpers.pgn_path)

# For game data
all_offsets = []
all_gamelinks = []
offsets = []
gamelinks = []

# For 'candidate' sac data
can_ucis = []
can_links = []
can_movetext = []
can_fens = []


# Scan PGN headers for faster parsing
while True:
    offset = pgn.tell()
    headers = chess.pgn.read_headers(pgn)
    if headers is None:
        break
    else:
        all_offsets.append(offset)
        all_gamelinks.append(headers["Site"])

# Pick a specific set of games to check, based on choices.py
if choices.sample_games:
    ## Sample games from input PGN
    print(f"Sampling {choices.sample_size} games...")
    print("")
    offsets = random.sample(all_offsets, choices.sample_size)
    for i in offsets:
        gamelinks.append(all_gamelinks[all_offsets.index(i)])
elif choices.sample_by_ids:
    ## Select games by Lichess game ID
    print("Sampling games by specific game ID...")
    selected_ids = choices.sample_ids
    for i in selected_ids:
        offsets.append(all_offsets[all_gamelinks.index(f"{'https://lichess.org/'}{i}")])
        gamelinks.append(f"{'https://lichess.org/'}{i}")
    print(f"{len(gamelinks)} to check...")
    print("")
else:
    ## Select all games in input PGN
    offsets = all_offsets
    gamelinks = all_gamelinks

print(f"About to check {len(offsets)} games (from {len(all_offsets)} games in the "
      f"input PGN)")
print('')

# Check each move of each game in the sample or PGN file
for offset in tqdm(offsets):

    pgn.seek(offset)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    for n in game.mainline():

        # Since we're looking here for Greek gift sacrifices by White
        # Ignore first, last, or penultimate plies
        # Ignore any moves that aren't listed as Bxh7 or Bxh6 where a White
        # bishop captures a Black pawn
        if not (n.ply() == 1 or n.turn() or n.is_end() or n.next().is_end()) \
                and \
                n.san() in {"Bxh7+", "Bxh7", "Bxh6+", "Bxh6"} and \
                board.is_capture(board.parse_san(n.san())) and \
                board.piece_at(n.move.to_square).symbol() == "p" and \
                n.next().turn():

            board.push(n.move)

            # Now check for Black follow-up captures by a pawn or the king
            if board.is_capture(board.parse_san(n.next().san())) and\
                    board.piece_at(n.next().move.to_square).symbol() in {"B"} and \
                    board.piece_at(n.next().move.from_square).symbol() in {"k","p"}:

                can_ucis.append(n.uci())
                can_fens.append(n.parent.board().fen())
                can_links.append(f"{game.headers['Site']}#{n.ply()}")

        else:
            board.push(n.move)
            continue

# After checking all moves in all games...
# Report # of identified candidates
print('')
print(f"Finished checking {len(offsets)} / {len(all_offsets)} games!")
print(f"Found {len(can_ucis)} probable Greek gift sacrifice(s)")
print(f"{can_links}")

# TODO: assess Greek gift sac quality using SF 14.1

# Save candidate details to a spreadsheet
candidates_out = pd.DataFrame(data = {"link": can_links})
with pd.ExcelWriter(f"outputs/{task_label}_{now_label}.xlsx") as writer:
    candidates_out.to_excel(writer, sheet_name=f"{task_label}")
print(f"Saved results in outputs/{task_label}_{now_label}.xlsx")
print('')
print('--- end ---')


