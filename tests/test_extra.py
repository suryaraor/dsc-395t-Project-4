from itertools import combinations

from consts import Color, NUM_NODES
from sim_board import GameBoard
from player2 import Player2, _top_moves_by_set_count
from .test_helpers import create_board, generate_fig4_board, moveset_equal


def remove_edge(board, edge) -> None:
    i, j = edge
    board[i][j] = Color.NONE
    board[j][i] = Color.NONE


def remove_node(board, node) -> None:
    for k in range(NUM_NODES):
        remove_edge(board, (node, k))


def nodes_of(board) -> set[int]:
    return {i for i in range(NUM_NODES) if any(c != Color.NONE for c in board[i])}


# GameBoard

def test_new_board_shape() -> None:
    board = GameBoard().board
    for i in range(NUM_NODES):
        for j in range(NUM_NODES):
            assert board[i][j] == (Color.NONE if i == j else Color.UNCOLORED)


def test_color_edge_is_symmetric() -> None:
    game = GameBoard()
    game.color_edge((5, 0), Color.P1)
    assert game.board[0][5] == Color.P1 and game.board[5][0] == Color.P1


def test_winner_is_opponent_of_triangle_owner() -> None:
    assert create_board([(0, 1), (1, 2)], [(3, 4)]).get_winner() is None
    assert create_board([(0, 1), (1, 2), (0, 2)], []).get_winner() == Color.P2
    assert create_board([], [(3, 4), (4, 5), (3, 5)]).get_winner() == Color.P1


# Allowed moves and sets

def test_fig2_allowed_moves() -> None:
    board = create_board([(0, 5), (0, 3)], [(2, 5)]).board
    p1 = Player2.get_allowed_moves(Color.P1, board)
    p2 = Player2.get_allowed_moves(Color.P2, board)
    assert (3, 5) in p2 and (3, 5) not in p1
    assert (4, 5) in p1 and (4, 5) in p2


def test_fig3_allowed_set_excludes_triangle_pair() -> None:
    board = create_board([(0, 5), (0, 3)], [(2, 5)]).board
    for allowed_set in Player2.get_maximal_allowed_sets(Color.P2, board):
        assert not {(3, 5), (2, 3)} <= allowed_set


def test_allowed_moves_skip_removed_edges() -> None:
    board = GameBoard().board
    remove_edge(board, (0, 1))
    assert (0, 1) not in Player2.get_allowed_moves(Color.P2, board)


def test_fig6_maximal_p1_sets() -> None:
    miniboard = generate_fig4_board("b").board
    sets = Player2.get_maximal_allowed_sets(Color.P1, miniboard)
    assert len(sets) == 1
    assert moveset_equal(frozenset([(0, 1), (0, 2), (0, 3)]), sets.pop())


def test_empty_board_has_ten_maximal_sets() -> None:
    # On an empty K6 the largest triangle-free edge sets are the 10 complete bipartite K3,3s.
    expected = set()
    for left in combinations(range(NUM_NODES), 3):
        right = [n for n in range(NUM_NODES) if n not in left]
        expected.add(frozenset((min(a, b), max(a, b)) for a in left for b in right))
    assert len(expected) == 10
    assert Player2.get_maximal_allowed_sets(Color.P2, GameBoard().board) == expected


def test_maximal_sets_with_no_allowed_moves() -> None:
    board = create_board([(0, 1), (1, 2)], [])
    for i, j in combinations(range(NUM_NODES), 2):
        if board.board[i][j] == Color.UNCOLORED and (i, j) != (0, 2):
            remove_edge(board.board, (i, j))
    assert Player2.get_allowed_moves(Color.P1, board.board) == []
    assert Player2.get_maximal_allowed_sets(Color.P1, board.board) == {frozenset()}


# Miniboard

def test_empty_board_miniboard_is_one_edge() -> None:
    miniboard = Player2.get_miniboard(GameBoard().board)
    assert miniboard is not None
    edges = [(i, j) for i in range(NUM_NODES) for j in range(i + 1, NUM_NODES)
             if miniboard[i][j] != Color.NONE]
    assert len(edges) == 1
    assert edges[0] in Player2.get_allowed_moves(Color.P2, miniboard)


def test_miniboard_is_complete_when_an_edge_is_removed() -> None:
    board = create_board([(0, 1)], []).board
    remove_edge(board, (0, 2))
    miniboard = Player2.get_miniboard(board)
    assert miniboard is not None
    nodes = nodes_of(miniboard)
    assert {0, 1} <= nodes and len(nodes) == 3 and 2 not in nodes
    for i, j in combinations(sorted(nodes), 2):
        assert miniboard[i][j] != Color.NONE


def test_miniboard_with_two_removed_nodes() -> None:
    board = create_board([(0, 1)], []).board
    remove_node(board, 4)
    remove_node(board, 5)
    miniboard = Player2.get_miniboard(board)
    assert miniboard is not None
    # Either third node gives a valid miniboard.
    assert nodes_of(miniboard) in ({0, 1, 2}, {0, 1, 3})


def test_miniboard_none_when_no_p2_allowed_move() -> None:
    # Fig. 5c: nodes 1-4 with every remaining edge blocked for blue.
    board = generate_fig4_board("b").board
    remove_node(board, 0)
    assert Player2.get_miniboard(board) is None


def test_miniboard_none_for_blue_k33() -> None:
    left, right = (0, 1, 2), (3, 4, 5)
    board = create_board([], [(a, b) for a in left for b in right]).board
    for side in (left, right):
        for edge in combinations(side, 2):
            remove_edge(board, edge)
    assert Player2.get_miniboard(board) is None


# Strategy steps

def test_top_moves_by_set_count_handout_example() -> None:
    # Handout 2.3.2: two maximal P1 sets, (0, 1) appears in both.
    sets = {frozenset([(0, 1), (0, 2), (0, 3)]), frozenset([(0, 1), (0, 2), (0, 4)])}
    assert _top_moves_by_set_count([(0, 1), (0, 3), (0, 4)], sets) == [(0, 1)]


def test_top_moves_by_set_count_keeps_every_tied_move() -> None:
    sets = {frozenset([(0, 1), (0, 2), (0, 3)]), frozenset([(0, 1), (0, 2), (0, 4)])}
    assert _top_moves_by_set_count([(0, 3), (0, 4)], sets) == [(0, 3), (0, 4)]


def test_fig6_get_move_on_miniboard() -> None:
    # Fig. 6: on miniboard M the strategy picks (0, 1) or (0, 3). M is its own only miniboard.
    board = generate_fig4_board("b").board
    assert Player2.get_move(board) in [(0, 1), (1, 0), (0, 3), (3, 0)]


def test_step2_single_allowed_move() -> None:
    # Miniboard {0,1,2,3}: (1,3) is the only uncolored edge, and it is P2-allowed.
    board = create_board([(0, 1), (0, 3), (2, 3)], [(0, 2), (1, 2)]).board
    assert Player2.get_allowed_moves(Color.P2, Player2.get_miniboard(board)) == [(1, 3)]
    assert Player2.get_move(board) in [(1, 3), (3, 1)]


def test_step3_decides() -> None:
    # Nodes 4 and 5 are removed so the miniboard must be {0,1,2,3}.
    # Maximal P2 sets are {(0,3),(1,3)} and {(1,3),(2,3)}, so step 3 picks (1,3).
    board = create_board([(0, 1), (1, 2)], [(0, 2)]).board
    remove_node(board, 4)
    remove_node(board, 5)
    assert Player2.get_move(board) in [(1, 3), (3, 1)]


def test_step4_breaks_three_way_tie() -> None:
    # Miniboard {0,1,2,3}. Step 3 ties (1,2), (1,3), (2,3). (1,2) is not P1-allowed and the
    # only maximal P1 set is {(1,3),(2,3)}, so skipping step 4 would wrongly return (1,2).
    board = create_board([(0, 1), (0, 2)], [(0, 3)]).board
    assert Player2.get_move(board) in [(1, 3), (3, 1), (2, 3), (3, 2)]


def test_step4_overrides_first_candidate() -> None:
    # Miniboard {0,1,2,4}. (0,2) is not P2-allowed (it closes blue 0-2-4), and (1,2) with (1,4)
    # would close blue 1-2-4, so the maximal P2 sets are {(1,2)} and {(1,4)} and step 3 ties.
    # Maximal P1 sets are {(0,2),(1,4)} and {(1,2),(1,4)}, so step 4 picks (1,4).
    # Skipping step 4 would return (1,2), the first tied candidate.
    board = create_board([(0, 1)], [(0, 4), (2, 4)]).board
    assert Player2.get_move(board) in [(1, 4), (4, 1)]


def test_get_move_does_not_mutate_board() -> None:
    board = create_board([(4, 3), (4, 2), (4, 1)], [(3, 2), (2, 1)]).board
    snapshot = [row[:] for row in board]
    Player2.get_move(board)
    assert board == snapshot


def test_player2_never_loses() -> None:
    """
    Safety net, not a strategy check: try every P1 move at every reachable position and make sure
    P2 always answers with a legal move and never completes a blue triangle.
    """
    seen = set()

    def explore(board) -> None:
        key = tuple(c.value for row in board for c in row)
        if key in seen:
            return
        seen.add(key)
        for i in range(NUM_NODES):
            for j in range(i + 1, NUM_NODES):
                if board[i][j] != Color.UNCOLORED:
                    continue
                game = GameBoard()
                game.board = [row[:] for row in board]
                game.color_edge((i, j), Color.P1)
                if game.get_winner() is not None:
                    continue  # P1 completed a red triangle
                a, b = Player2.get_move(game.board)
                assert game.board[a][b] == Color.UNCOLORED
                game.color_edge((a, b), Color.P2)
                assert game.get_winner() != Color.P1
                if game.get_winner() is None:
                    explore(game.board)

    explore(GameBoard().board)
