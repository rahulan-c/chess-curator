"""Helper functions for chess-curator."""

import chess
import chess.engine
import requests
import time

import choices

engine_path = "engine/stockfish_22031308_x64_avx2/stockfish_22031308_x64_avx2.exe"
pgn_path = f"inputs/{choices.filename}"

def read_pgn(pgn_path):
    """Read PGN file."""
    pgn = open(pgn_path)
    return pgn

def evaluate_move(fen: str,
                  played: str,
                  time_per_move: int = 3,
                  engine_path: str = engine_path):
    """ Evaluate a move played in a position with an engine.

    :param fen: FEN of position preceding move
    :param played: move that was played in UCI format
    :param time_per_move: number of seconds the engine should spend analysing
        the position. Default value: 3.
    :param engine_path: path to engine's .exe file.

    :return: cpl
    """
    mate_thresh = 100000
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    board = chess.Board(fen)
    info = engine.analyse(board,
                          multipv=1,
                          limit=chess.engine.Limit(time=time_per_move))
    engine.quit()
    # TODO: finish!
    return None

def check_if_move_is_uniquely_nonlosing(fen: str,
                                        played: str,
                                        num_engine_moves: int = 5,
                                        time_per_move: int = 3,
                                        engine_path: str = engine_path):
    """ Assess whether a move played in a position is the only non-losing move
    according to a locally saved engine.

    :param fen: FEN of position preceding move
    :param played: move that was played, in UCI format
    :param num_engine_moves: max number of engine moves to return. Default
        value: 5.
    :param time_per_move: number of seconds the engine should spend analysing
        the position. Default value: 3.
    :param engine_path: path to engine's .exe file.

    :return: True or False
    """
    mate_thresh = 100000

    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    board = chess.Board(fen)
    info = engine.analyse(board, multipv=num_engine_moves,
                          limit=chess.engine.Limit(time=time_per_move))
    engine.quit()
    other_nonlosing = []
    top_move = board.san(info[0]['pv'][0])
    top_eval = info[0]['score'].pov(board.turn).score(mate_score=mate_thresh)
    played_matches_top = True if board.san(
        board.parse_uci(played)) == top_move else False

    if not played_matches_top:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        board = chess.Board(fen)
        move_info = engine.analyse(board,
                                   chess.engine.Limit(time=time_per_move),
                                   root_moves=[chess.Move.from_uci(played)])
        played_eval = move_info["score"].pov(board.turn).score(
            mate_score=mate_thresh)
        engine.quit()
        played_cpl = (played_eval - top_eval) * -1  # show as positive number
    else:
        played_eval = top_eval
        played_cpl = 0

    for m in range(len(info)):
        move = board.san(info[m]['pv'][0])
        move_eval = info[m]['score'].pov(board.turn).score(
            mate_score=mate_thresh)
        move_cpl = (move_eval - top_eval) * -1
        move_vs_played = move_cpl - played_cpl
        matches_played = True if board.san(
            board.parse_uci(played)) == move else False
        losing = True if move_eval <= -300 else False
        worse_than_played = True if move_vs_played > 300 else False
        if not matches_played and not losing and not worse_than_played:
            other_nonlosing.append(move)

    if len(other_nonlosing) == 0:
        return True
    else:
        return False


def check_position_against_masters_db(fen: str):
  """ Check FEN for matching Lichess Masters DB games.

  :param fen: the position to check, in FEN format.
  :return: matches: the number of Lichess Masters database games that reached
  the input position.
  """
  # How long to wait between DB queries
  pause_queries = 0.5  # between each query
  pause_429 = 10       # after a 429 error is raised

  fendict = {}
  cachedfen = fendict.get(fen)
  if cachedfen:
    r = cachedfen
  else:
    while True:
      payload = {'fen': fen, 'topGames': 0, 'moves': 30}
      r = requests.get(f'https://explorer.lichess.ovh/master', params = payload)
      if r.status_code == 200:
        time.sleep(pause_queries)
        r = r.json()
        break
      if r.status_code == 429:
        print(f"Pausing for {pause_429} seconds")
        time.sleep(pause_429)
        continue
    matches = r['white'] + r['black'] + r['draws']
  return matches