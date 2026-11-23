from extension.board_utils import list_legal_moves_for, copy_piece_move
import time

''' notes to self:
    
print(piece.position) seems to return row-column (0-1, 3-4 etc)—They're NOT pairs, but should be able to use str()
https://chessprogramming.org/Iterative_Deepening  (for later)

Maybe come back to this if you do PST eval: https://www.talkchess.com/forum/viewtopic.php?t=50840 [1]

'''


def check_board(board, player) -> int:
    weights = {
        "Pawn_Q": 90,
        "Pawn": 10,
        "Knight": 30,
        "Bishop": 30,
        "Right": 50,
        "Queen": 90,
        "King": 1000,
    }

    # ++centre control but --corners (adapted from Tomasz Michniewksi [1] for Kn/Q/B
    centre_pst = [
        [-5, -4, -3, -4, -5],
        [-4, 0, 5, 0, -4],
        [-3, 5, 10, 5, -3],
        [-4, 0, 5, 0, -4],
        [-5, -4, -3, -4, -5]
    ]

    king_pst = [
        [5, 0, -5, 0, 5],
        [0, -2, -5, -2, 0],
        [-5, -5, -20, -5, -5],
        [0, -2, -5, -2, 0],
        [5, 0, -5, 0, 5]
    ]

    blocked = [0, 0, 0, 0, 0]
    w_pawn_pst = [
        [5, 5, 5, 5, 5],
        [3, 3, 4, 3, 3],
        [1, 1, 2, 1, 1],
        blocked,  # start
        blocked
    ]

    b_pawn_pst = [
        blocked,
        blocked,  # start
        [1, 1, 1, 1, 1],
        [2, 2, 3, 2, 2],
        [5, 5, 5, 5, 5]
    ]

    net_score = 0
    for p in board.players:
        for piece in list(board.get_player_pieces(p)):
            piece_name = type(piece).__name__

            r_s, c_s = str(piece.position).split("-")
            r, c = int(r_s), int(c_s)

            # THIS LOGIC AND THE LIST[LIST]s ABOVE CAN GO INTO A HELPER FUNCTION!
            pos_bonus = 0
            if piece_name in ["Knight", "Queen", "Bishop", "Right", "Pawn_Q"]:
                pos_bonus = centre_pst[r][c]
            elif piece_name == "King":
                pos_bonus = king_pst[r][c]
            elif piece_name == "Pawn":
                if p.name == "white":
                    pos_bonus = w_pawn_pst[r][c]
                else:
                    pos_bonus = b_pawn_pst[r][c]

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


def minimax(board, depth, is_maximising: bool, agent_player, b_time: int, alpha=-float("inf"), beta=float("inf")):
    if time.time() >= b_time:
        return None

    if depth == 0:
        return check_board(board, agent_player)

    if is_maximising:
        max_eval = -float("inf")
        poss_moves = get_possible_moves(board, agent_player)
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
        min_eval = float("inf")
        poss_moves = return_opponent_moves(board, agent_player)[1]
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


def ids_helper(board, player, max_depth: int, b_time: float):
    poss_moves = list_legal_moves_for(board, player)
    if not poss_moves:
        return None, None

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

    return best_piece, best_move


def agent(board, player, var):
    # print(f"Ply: {var[0]}")
    # print(f"Agent nmae: {player.name}")  # REMOVE BEFORE SUBMISSION???
    # print(f"Opponent is: {return_opponent_moves(board, player)[0].name}")

    b_time = time.time() + 10
    return ids_helper(board, player, max_depth=6, b_time=b_time)


''' MOVED ALL THIS FROM agent() TO ids_helper()

    best_score = -float("inf")
    best_piece, best_move = None, None

    poss_movies = list_legal_moves_for(board, player)
    if poss_movies:
        for p_piece, p_move_opt in poss_movies:

            testing_board = test_move(board, p_piece, p_move_opt)

            if testing_board is None:
                continue

            score = minimax(testing_board, 2, False, player, best_score)

            if score > best_score:
                best_score, best_piece, best_move = score, p_piece, p_move_opt

        return best_piece, best_move

    else:
        return None, None
'''
