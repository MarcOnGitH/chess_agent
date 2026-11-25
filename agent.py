from extension.board_utils import list_legal_moves_for, copy_piece_move
import time

''' notes to self:

print(piece.position) seems to return row-column (0-1, 3-4 etc)—They're NOT pairs, but should be able to use str()
https://chessprogramming.org/Iterative_Deepening  (for later)

Maybe come back to this if you do PST eval: https://www.talkchess.com/forum/viewtopic.php?t=50840 [1]

a "smarter" move ordering algorithm: https://chessprogramming.org/MVV-LVA
https://chessprogramming.org/Quiescence_Search

'''

weights = {
    "Pawn_Q": 90,
    "Pawn": 10,
    "Knight": 30,
    "Bishop": 30,
    "Right": 75,
    "Queen": 90,
    "King": 1000,
}

# ++centre control but --corners (adapted from Tomasz Michniewksi [1] for Kn/Q/B
flatten = [0, 0, 0, 0, 0]
centre_pst = [
    [-5, -4, -3, -4, -5],
    [-4, 0, 5, 0, -4],
    [-3, 5, 10, 5, -3],
    [-4, 0, 5, 0, -4],
    [-5, -4, -3, -4, -5]
]

king_pst = [
    flatten,
    [-2, -4, -6, -4, -2],
    [-5, -5, -20, -5, -5],
    [-2, -4, -6, -4, -2],
    flatten
]

w_pawn_pst = [
    [5, 5, 5, 5, 5],
    [3, 3, 4, 3, 3],
    [1, 1, 2, 1, 1],
    flatten,  # start
    flatten
]

b_pawn_pst = [
    flatten,
    flatten,  # start
    [1, 1, 1, 1, 1],
    [2, 2, 3, 2, 2],
    [5, 5, 5, 5, 5]
]

game_history = set()


def get_pos_key(board) -> tuple:
    pieces = []
    for p in board.get_pieces():
        pieces.append((type(p).__name__, p.player.name,
                      p.position.x, p.position.y))
    pieces.sort()
    return tuple(pieces)


def check_board(board, player) -> int:
    net_score = 0
    for p in board.players:
        for piece in list(board.get_player_pieces(p)):
            piece_name = type(piece).__name__

            row, col = piece.position.y, piece.position.x

            # THIS LOGIC AND THE LIST[LIST]s ABOVE CAN GO INTO A HELPER FUNCTION!
            pos_bonus = 0
            if piece_name in ["Knight", "Queen", "Bishop", "Right", "Pawn_Q"]:
                pos_bonus = centre_pst[row][col]
            elif piece_name == "King":
                pos_bonus = king_pst[row][col]
            elif piece_name == "Pawn":
                if p.name == "white":
                    pos_bonus = w_pawn_pst[row][col]
                else:
                    pos_bonus = b_pawn_pst[row][col]

            piece_wt = weights.get(piece_name)
            if p.name == player.name:
                net_score += piece_wt + pos_bonus
            else:
                net_score -= piece_wt + pos_bonus

    return net_score


def test_move(board, piece, move_opt):
    temp_board = board.clone()
    testing_board, testing_piece, testing_move = copy_piece_move(
        temp_board, piece, move_opt)  # (b,p,m)

    if testing_piece and testing_move:
        try:
            testing_piece.move(testing_move)
        except Exception:
            return None  # DONT FORGET TO HANDLE THIS CASE IF/WHEN YOU CALL THIS FUNC LATER!!!

    return testing_board


def get_possible_moves(board, player) -> list:
    poss_moves = list_legal_moves_for(board, player)
    return poss_moves


def return_opponent_moves(board, agent_player):
    for p in board.players:
        if p.name != agent_player.name:
            opponent = p
            opponent_moves = get_possible_moves(board, opponent)
    # returning p in-case I ever need it, though I've yet to use it so far
    return (p, opponent_moves)


#
def get_score(capture):
    return capture[0]


def order_mvs(board, poss_moves: list) -> list:
    captures = []
    others = []
    pos_to_val = {}

    for p in board.get_pieces():
        pos = (p.position.x, p.position.y)
        val = weights.get(type(p).__name__)
        pos_to_val[pos] = val

    for piece, move in poss_moves:
        if move.captures:
            victim_val = pos_to_val.get((move.position.x, move.position.y), 10)
            attacker_val = weights.get(type(piece).__name__)
            score = (victim_val * 10) - attacker_val
            captures.append((score, (piece, move)))
        else:
            others.append((piece, move))
    # needs sorting and unpack

    sorted_captures = []
    captures.sort(key=get_score, reverse=True)
    for score, moves in captures:
        sorted_captures.append(moves)

    return sorted_captures + others


# for q_s, standard pat forms a basecase? need to verify this
# based of the yt videos algorithm — parameter may need refining
def quiescence(board, is_maximising: bool, agent_player, b_time: float, alpha: float, beta: float, q_depth: int = 4):
    if time.time() >= b_time:
        return None

    stand_pat = check_board(board, agent_player)
    if q_depth == 0:
        return stand_pat

    if is_maximising:
        if stand_pat >= beta:
            return stand_pat
        if stand_pat >= alpha:
            alpha = stand_pat

        # continue...


def minimax(board, depth, is_maximising: bool, agent_player, b_time: int, alpha=-float("inf"), beta=float("inf")):
    if time.time() >= b_time:
        return None

    if get_pos_key(board) in game_history:
        return 0  # avd

    if depth == 0:
        return check_board(board, agent_player)

    if is_maximising:
        poss_moves = get_possible_moves(board, agent_player)
        if not poss_moves:
            return (-100000-depth)

        poss_moves = order_mvs(board, poss_moves)
        max_eval = -float("inf")
        for moves in poss_moves:
            piece, move = moves
            tmp_board = test_move(board, piece, move)

            if tmp_board is not None:
                next_eval = minimax(tmp_board, depth - 1,
                                    False, agent_player, b_time, alpha, beta)
                if next_eval is None:
                    return None
                max_eval = max(max_eval, next_eval)
                alpha = max(alpha, next_eval)
                if beta <= alpha:
                    break
            else:
                continue
        return max_eval

    else:
        poss_moves = return_opponent_moves(board, agent_player)[1]
        if not poss_moves:
            return (+100000 + depth)

        poss_moves = order_mvs(board, poss_moves)
        min_eval = float("inf")
        for moves in poss_moves:
            piece, move = moves
            tmp_board = test_move(board, piece, move)

            if tmp_board is not None:
                next_eval = minimax(tmp_board, depth - 1,
                                    True, agent_player, b_time, alpha, beta)
                if next_eval is None:
                    return None
                min_eval = min(min_eval, next_eval)
                beta = min(beta, next_eval)
                if beta <= alpha:
                    break
            else:
                continue
        return min_eval


def is_winning_checkmate(score: int) -> bool:
    return score >= 100000


def ids_helper(board, player, max_depth: int, b_time: float):
    poss_moves = list_legal_moves_for(board, player)
    if not poss_moves:
        return None, None

    poss_moves = order_mvs(board, poss_moves)
    best_piece, best_move = poss_moves[0]

    for curr_depth in range(max_depth):
        if time.time() >= b_time:
            break

        d_best_score = -float("inf")
        d_best_piece, d_best_move = None, None
        timed_out = False

        for piece, move in poss_moves:
            testing_board = test_move(board, piece, move)
            if testing_board is None:
                continue

            score = minimax(testing_board, curr_depth, False,
                            player, b_time, alpha=d_best_score)

            if score is None:
                timed_out = True
                break

            if score > d_best_score:
                d_best_score, d_best_piece, d_best_move = score, piece, move

        if timed_out:
            break

        if d_best_piece is not None:
            best_piece, best_move = d_best_piece, d_best_move
            best_moves = (best_piece, best_move)
            if best_moves in poss_moves:
                poss_moves.remove(best_moves)
                poss_moves.insert(0, best_moves)

            if is_winning_checkmate(d_best_score):
                break

    return best_piece, best_move


# <=2 captures both cases (B v W)
def agent(board, player, var):
    if var[0] <= 2:
        game_history.clear()
    game_history.add(get_pos_key(board))

    b_time = time.time() + 8
    return ids_helper(board, player, max_depth=12, b_time=b_time)
