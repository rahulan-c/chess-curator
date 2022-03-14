"""Identify sacs in games."""

import random

import chess
import pandas as pd
from chess.pgn import ChildNode
from tqdm import tqdm

import choices
import helpers
import utils
from helpers import read_pgn, check_if_move_is_uniquely_nonlosing, \
    check_position_against_masters_db

# Helpers and parameters
material_adv_threshold = 2
winning_eval_threshold = 300
gamelink_prefix = "https://lichess.org/"

# Read PGN file
pgn = read_pgn(helpers.pgn_path)

# For game data
all_offsets = []
all_gamelinks = []
offsets = []
gamelinks = []

# For 'candidate' sac data
can_ucis = []
can_svgs = []
can_links = []
can_white = []
can_black = []
can_movetext = []

# For rejected candidate data
forks = []
skewers = []
abspinned = []
onlynonlosing = []
trapped = []
theory = []

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
        offsets.append(all_offsets[all_gamelinks.index(f"{gamelink_prefix}{i}")])
        gamelinks.append(f"{gamelink_prefix}{i}")
    print(f"{len(gamelinks)} to check...")
    print("")
else:
    ## Select all games in input PGN
    offsets = all_offsets
    gamelinks = all_gamelinks

print(f"About to check {len(offsets)} games (from {len(all_offsets)} games in the "
      f"input PGN)")
print('')

# For each selected game...
for offset in tqdm(offsets):

    pgn.seek(offset)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    # # Print game info
    # print('')
    # print(f"{game.headers['White']} vs {game.headers['Black']} ({game.headers['Result']})")
    # print(f"{game.headers['Site']}")
    # print("")

    last_ply = game.end().ply()

    # Check each move from first to last...
    for n in game.mainline():

        # Ignore moves before ply 7
        if n.ply() <= 6:
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore moves that are either too close to the end or over ply 200
        # (since Lichess's server analysis only extends to ply 200)
        if n.ply() > last_ply - 6 or n.ply() >= 200:
            break

        # Identify the candidate move, the pre-candidate position, and the
        # side that played the candidate move
        can: ChildNode = n.parent
        precan: ChildNode = n.parent.parent
        side = 1 if precan.board().turn else 0

        # Ignore moves played in objectively winning positions or when
        # significantly ahead in material
        if abs(can.eval().pov(side).score(mate_score=100000)) > winning_eval_threshold or \
                utils.material_diff(precan.board(), side) >= material_adv_threshold:
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore non-captures
        if not board.is_capture(board.parse_san(n.san())):
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore en passant captures
        if board.is_en_passant((board.parse_san(n.san()))):
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore pawn captures
        if board.piece_at(n.move.to_square).symbol() in {'P', 'p'}:
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore moves when in check
        if precan.board().is_check():
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore moves immediately after a promotion
        if can.move.promotion:
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore castling moves
        if utils.is_castling(can):
            board.push(n.move)
            last_move = n.move
            continue

        # Ignore captures of a side's last non-pawn piece (when they also have
        # < 4 pawns)
        nonpawns = len(board.pieces(2, precan.board().turn)) + \
                   len(board.pieces(3, precan.board().turn)) + \
                   len(board.pieces(4, precan.board().turn)) + \
                   len(board.pieces(5, precan.board().turn))
        pawns = len(board.pieces(1, precan.board().turn))
        if nonpawns == 1 and pawns < 4:
            board.push(n.move)
            last_move = n.move
            continue

        # Identify the move after the post-candidate capture
        child = n.next() if not n.next().is_end() else None

        # Compute the candidate move's CPL
        can_cpl = can.eval().pov(side).score(
            mate_score=100000) - precan.eval().pov(side).score(
            mate_score=100000)

        # Compute change in eval for candidate colour
        # Between the position 2 plies after the candidate and that before the candidate
        # If this is higher than the loss in material to this point, reject
        # If the material balance is positive or even after 2 plies, reject
        after_two_cpl = child.eval().pov(side).score(
            mate_score=100000) - precan.eval().pov(side).score(
            mate_score=100000)
        after_two_mat_diff = (utils.material_diff(child.board(),
                                                  side) - utils.material_diff(
            precan.board(), side)) * 100
        after_two_mat_bal = utils.material_diff(child.board(), side)

        # Reject cases where after 2 plies,
        # material difference >= 0
        # candidate CPL >= material loss
        if after_two_mat_diff >= 0 or \
                after_two_cpl * -1 > after_two_mat_diff * -1 or \
                after_two_mat_bal >= 0:
            board.push(n.move)
            last_move = n.move
            continue

        # Reject candidates where material is restored after 4 plies
        grandchild = child.next()
        grandchild2 = grandchild.next()

        # Compute change in eval for candidate colour
        # Between the position 4 plies after the candidate and that before the candidate
        # If this is higher than the loss in material to this point, reject
        after_four_cpl = grandchild2.eval().pov(side).score(
            mate_score=100000) - precan.eval().pov(side).score(
            mate_score=100000)
        after_four_mat_diff = (utils.material_diff(grandchild2.board(),
                                                   side) - utils.material_diff(
            precan.board(), side)) * 100
        after_four_mat_bal = utils.material_diff(grandchild2.board(), side)

        if after_four_mat_diff >= 0 or \
                after_four_cpl * -1 > after_four_mat_diff * -1 or \
                after_four_mat_bal >= 0:
            board.push(n.move)
            last_move = n.move
            continue

        # Reject candidates where material is restored after 6 plies
        grandchild3 = grandchild2.next()
        grandchild4 = grandchild3.next()

        # Compute change in eval for candidate colour
        # Between the position 6 plies after the candidate and that before the candidate
        # If this is higher than the loss in material to this point, reject
        after_six_cpl = grandchild4.eval().pov(side).score(
            mate_score=100000) - precan.eval().pov(side).score(
            mate_score=100000)
        after_six_mat_diff = (utils.material_diff(grandchild4.board(),
                                                  side) - utils.material_diff(
            precan.board(), side)) * 100
        after_six_mat_bal = utils.material_diff(grandchild4.board(), side)

        if after_six_mat_diff >= 0 or \
                after_six_cpl * -1 > after_six_mat_diff * -1 or \
                after_six_mat_bal >= 0:
            board.push(n.move)
            last_move = n.move
            continue

        # Now apply some advanced checks...

        # Reject captures of absolutely pinned pieces
        if utils.captured_piece_was_abs_pinned(n):
            abspinned.append(
                f"{game.headers['Site'] + '#' + str(precan.ply() + 1)}")
            board.push(n.move)
            last_move = n.move
            continue

        # Reject captures of trapped pieces
        if utils.trapped_piece(n):
            trapped.append(
                f"{game.headers['Site'] + '#' + str(precan.ply())}")
            board.push(n.move)
            last_move = n.move
            continue

        # Reject captures of skewered pieces
        if utils.skewer(n):
            skewers.append(f"{game.headers['Site'] + '#' + str(precan.ply() + 1)}")
            board.push(n.move)
            last_move = n.move
            continue

        # Reject captures of forked pieces
        if utils.fork(precan):
            forks.append(f"{game.headers['Site'] + '#' + str(precan.ply())}")
            board.push(n.move)
            last_move = n.move
            continue
        # NB the fork method needs to be extended to avoid excluding certain
        # kinds of valid sac that can arise after a fork

        # TODO: only consider candidates from objectively undecided positions

        # TODO: skip piece captures resulting from a double attack (and the
        #  captured piece was one of the attacked pieces)

        # TODO: skip piece captures if a defender of the captured piece was
        #  forced to move away from the defence in the last move.

        # Reject candidates that can be found in the Lichess Masters DB
        # Min. 3 matching games
        if check_position_against_masters_db(board.fen()) >= 3:
            theory.append(f"{game.headers['Site'] + '#' + str(precan.ply() + 1)}")
            board.push(n.move)
            last_move = n.move
            continue

        # Reject candidates considered by the engine to be the only non-losing
        # move in the position
        if check_if_move_is_uniquely_nonlosing(fen = precan.board().fen(),
                                               played = can.uci()):
            onlynonlosing.append(f"{game.headers['Site'] + '#' + str(precan.ply() + 1)}")
            board.push(n.move)
            last_move = n.move
            continue


        # Save remaining candidate details
        can_ucis.append(can.uci())
        movenum = ((precan.ply() - 1) // 2) + 1
        movetext = str(movenum) + '. ' + can.san() if side else str(
            movenum) + '...' + can.san()
        can_movetext.append(movetext)
        can_links.append(game.headers['Site'] + '#' + str(precan.ply() + 1))
        can_white.append(game.headers['White'])
        can_black.append(game.headers['Black'])

        # TODO: tag candidates by characteristics (eg by game phase, by sacd'
        #  piece [tag exchange sacs separately], by quality...)

        # Fetch next move
        board.push(n.move)
        # Update previous position parameters
        last_move = n.move


# After checking all moves in all games...
# Report # of identified candidates
print('')
print(f"Finished checking {len(offsets)} / {len(all_offsets)} games!")
print(f"Found {len(can_ucis)} candidate sac(s)")
print(f"{can_links}")

# Save candidate move and selected rejected move details to a spreadsheet
candidates_out = pd.DataFrame(data = {
    "link": can_links,
    "move": can_movetext})
forks_out = pd.DataFrame(data = {"forks": forks})
skewers_out = pd.DataFrame(data = {"skewers": skewers})
abspinned_out = pd.DataFrame(data = {"abs_pinned": abspinned})
onlynonlosing_out = pd.DataFrame(data = {"only_nonlosing": onlynonlosing})
trapped_out = pd.DataFrame(data = {"trapped": trapped})
theory_out = pd.DataFrame(data = {"theory": theory})

with pd.ExcelWriter("outputs/results.xlsx") as writer:
    candidates_out.to_excel(writer, sheet_name="CANDIDATES")
    forks_out.to_excel(writer, sheet_name="forks")
    skewers_out.to_excel(writer, sheet_name="skewers")
    abspinned_out.to_excel(writer, sheet_name="abs_pinned")
    onlynonlosing_out.to_excel(writer, sheet_name="nonlosing")
    trapped_out.to_excel(writer, sheet_name="trapped")
    theory_out.to_excel(writer, sheet_name="theory")
print(f"Saved results in outputs./results.xlsx")
print('')
print('###########  END  ##############')


