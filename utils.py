"""Utility functions from lichess-puzzler.
https://github.com/ornicar/lichess-puzzler/blob/c8c1fe2ff40f22a7d8b2a65a8f9c51e22fa2e776/tagger/util.py
"""

from typing import List, Optional, Tuple
import chess
from chess import square_rank, Color, Board, Square, Piece, square_distance, WHITE, BLACK, SquareSet
from chess import KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN
from chess.pgn import ChildNode
from typing import Type, TypeVar

A = TypeVar('A')
def pp(a: A, msg = None) -> A:
    print(f'{msg + ": " if msg else ""}{a}')
    return a

def moved_piece_type(node: ChildNode) -> chess.PieceType:
    pt = node.board().piece_type_at(node.move.to_square)
    assert(pt)
    return pt

def is_advanced_pawn_move(node: ChildNode) -> bool:
    if node.move.promotion:
        return True
    if moved_piece_type(node) != chess.PAWN:
        return False
    to_rank = square_rank(node.move.to_square)
    return to_rank < 3 if node.turn() else to_rank > 4

def is_very_advanced_pawn_move(node: ChildNode) -> bool:
    if not is_advanced_pawn_move(node):
        return False
    to_rank = square_rank(node.move.to_square)
    return to_rank < 2 if node.turn() else to_rank > 5

def is_king_move(node: ChildNode) -> bool:
    return moved_piece_type(node) == chess.KING

def is_castling(node: ChildNode) -> bool:
    return is_king_move(node) and square_distance(node.move.from_square, node.move.to_square) > 1

def is_capture(node: ChildNode) -> bool:
    return node.parent.board().is_capture(node.move)

def next_node(node: ChildNode) -> Optional[ChildNode]:
    return node.variations[0] if node.variations else None

def next_next_node(node: ChildNode) -> Optional[ChildNode]:
    nn = next_node(node)
    return next_node(nn) if nn else None

values = { PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9 }
king_values = { PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 99 }
ray_piece_types = [QUEEN, ROOK, BISHOP]

def piece_value(piece_type: chess.PieceType) -> int:
    return values[piece_type]

def material_count(board: Board, side: Color) -> int:
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def material_diff(board: Board, side: Color) -> int:
    return material_count(board, side) - material_count(board, not side)

def attacked_opponent_pieces(board: Board, from_square: Square, pov: Color) -> List[Piece]:
    return [piece for (piece, _) in attacked_opponent_squares(board, from_square, pov)]

def attacked_opponent_squares(board: Board, from_square: Square, pov: Color) -> List[Tuple[Piece, Square]]:
    pieces = []
    for attacked_square in board.attacks(from_square):
        attacked_piece = board.piece_at(attacked_square)
        if attacked_piece and attacked_piece.color != pov:
            pieces.append((attacked_piece, attacked_square))
    return pieces

def is_defended(board: Board, piece: Piece, square: Square) -> bool:
    if board.attackers(piece.color, square):
        return True
    # ray defense https://lichess.org/editor/6k1/3q1pbp/2b1p1p1/1BPp4/rp1PnP2/4PRNP/4Q1P1/4B1K1_w_-_-_0_1
    for attacker in board.attackers(not piece.color, square):
        attacker_piece = board.piece_at(attacker)
        assert(attacker_piece)
        if attacker_piece.piece_type in ray_piece_types:
            bc = board.copy(stack = False)
            bc.remove_piece_at(attacker)
            if bc.attackers(piece.color, square):
                return True

    return False

def is_hanging(board: Board, piece: Piece, square: Square) -> bool:
    return not is_defended(board, piece, square)

def can_be_taken_by_lower_piece(board: Board, piece: Piece, square: Square) -> bool:
    for attacker_square in board.attackers(not piece.color, square):
        attacker = board.piece_at(attacker_square)
        assert(attacker)
        if attacker.piece_type != chess.KING and values[attacker.piece_type] < values[piece.piece_type]:
            return True
    return False

def is_in_bad_spot(board: Board, square: Square) -> bool:
    # hanging or takeable by lower piece
    piece = board.piece_at(square)
    assert(piece)
    return (bool(board.attackers(not piece.color, square)) and
            (is_hanging(board, piece, square) or can_be_taken_by_lower_piece(board, piece, square)))

def is_trapped(board: Board, square: Square) -> bool:
    if board.is_check() or board.is_pinned(board.turn, square):
        return False
    piece = board.piece_at(square)
    assert(piece)
    if piece.piece_type in [PAWN, KING]:
        return False
    if not is_in_bad_spot(board, square):
        return False
    for escape in board.legal_moves:
        if escape.from_square == square:
            capturing = board.piece_at(escape.to_square)
            if capturing and values[capturing.piece_type] >= values[piece.piece_type]:
                return False
            board.push(escape)
            if not is_in_bad_spot(board, escape.to_square):
                return False
            board.pop()
    return True

def attacker_pieces(board: Board, color: Color, square: Square) -> List[Piece]:
    return [p for p in [board.piece_at(s) for s in board.attackers(color, square)] if p]

# def takers(board: Board, square: Square) -> List[Tuple[Piece, Square]]:
#     # pieces that can legally take on a square
#     t = []
#     for attack in board.legal_moves:
#         if attack.to_square == square:
#             t.append((board.piece_at(attack.from_square), attack.from_square))
#     return t


###############################################################################

# ---- Additional tactics detection functions ---------------------------------


def trapped_piece(node: ChildNode) -> bool:
    """Check if a captured piece was previously trapped."""
    square = node.move.to_square
    captured = node.parent.board().piece_at(square)
    if captured and captured.piece_type != PAWN:
        prev = node.parent
        assert isinstance(prev, ChildNode)
        if prev.move.to_square == square:
            square = prev.move.from_square
        if is_trapped(prev.parent.board(), square):
            return True
    return False


def fork(node: ChildNode) -> bool:
    """Detect forks."""
    if moved_piece_type(node) is not KING:
        board = node.board()
        nb = 0
        if is_in_bad_spot(board, node.move.to_square):
            nb = 0
        for (piece, square) in attacked_opponent_squares(board, node.move.to_square, not node.turn()):
            if piece.piece_type == PAWN:
                continue
            if (
                king_values[piece.piece_type] > king_values[moved_piece_type(node)] or (
                    is_hanging(board, piece, square) and
                    square not in board.attackers(node.turn(), node.move.to_square)
                )
            ):
                nb += 1
        if nb > 1:
            return True
    return False


def skewer(node: ChildNode) -> bool:
    """Detect skewers."""
    prev = node.parent
    assert isinstance(prev, ChildNode)
    capture = prev.board().piece_at(node.move.to_square)
    # print(f"captured piece: {capture.symbol()}")
    if capture and moved_piece_type(node) in ray_piece_types and not node.board().is_checkmate():
        between = SquareSet.between(node.move.from_square, node.move.to_square)
        # print(f"between: {between}")
        op_move = prev.move
        # print(f"op_move: {op_move}")
        assert op_move
        if (op_move.to_square == node.move.to_square or not op_move.from_square in between):
            # continue
            # print(f":(")
            # print(f" condition 1: {op_move.to_square == node.move.to_square}")
            # print(f"condition 2: "
             #      f"{not op_move.from_square in between}")
            return False
        if (
            king_values[moved_piece_type(prev)] > king_values[capture.piece_type] and
            is_in_bad_spot(prev.board(), node.move.to_square)
        ):
            # print(":)")
            return True
    return False


def xray(node: ChildNode) -> bool:
    """Detect x-rays [unfinished]."""
    print(f"node: {node.san()}")
    print(f"is_capture(node): {is_capture(node)}")
    print("")
    print(f"prev_op_node: {node.parent}")
    print("")
    print(f"node.move.to_square: {chess.square_name(node.move.to_square)}")
    print(f"prev_op_node.move.to_square: "
          f"{chess.square_name(node.parent.move.to_square)}")
    if not is_capture(node):
        # continue
        pass
    prev_op_node = node.parent
    # assert isinstance(prev_op_node, ChildNode)
    if prev_op_node.move.to_square != node.move.to_square or moved_piece_type(prev_op_node) == KING:
        # continue
        pass
    prev_pl_node = prev_op_node.parent
    # assert isinstance(prev_pl_node, ChildNode)
    if prev_pl_node.move.to_square != prev_op_node.move.to_square:
        # continue
        pass
    if prev_op_node.move.from_square in SquareSet.between(node.move.from_square, node.move.to_square):
        return True
    return False


def captured_piece_was_abs_pinned(node: ChildNode) -> bool:
    """Check if a captured piece couldn't escape due to an absolute pin."""
    prev = node.parent.parent
    # assert isinstance(prev, ChildNode) or assert isinstance(GameNode)
    # print(f"Checking if the {'White' if node.turn() else 'Black'} piece on"
    #       f" {chess.square_name(node.move.to_square)} was pinned in FEN"
    #       f" {prev.board().fen()}")
    if prev.board().is_pinned(node.turn(), node.move.to_square):
        return True
    return False


