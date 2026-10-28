from __future__ import annotations
from collections import Counter
from itertools import combinations
from consts import Board, Color, Edge, NUM_NODES


class Player2:
    """
    Implements a winning strategy for the second player in a game of Sim
    """

    @staticmethod
    def get_move(board: Board) -> Edge:
        """
        Return a possible move for the second player (blue) that follows the optimal strategy laid out in the handout,
        given the input board state. If multiple moves are viable, this method can return any of them.

        Returns an edge (i, j) with i < j. Raises ValueError if the board has no miniboard
        (the handout says get_move is never called on such a board).
        """
        # selecting a miniboard (step 1, handout 2.3.2)
        mini_board = Player2.get_miniboard(board)
        if mini_board is None:
            # stopping here, since the handout promises this case never reaches get_move
            raise ValueError("no miniboard exists for this board, so the strategy has no move")

        # taking the move directly when only one P2-allowed move exists (step 2)
        p2_moves = Player2.get_allowed_moves(Color.P2, mini_board)
        if len(p2_moves) == 1:
            return p2_moves[0]

        # keeping the moves found in the most maximal P2-allowed sets (step 3)
        tied_moves = _top_moves_by_set_count(p2_moves, Player2.get_maximal_allowed_sets(Color.P2, mini_board))
        if len(tied_moves) == 1:
            return tied_moves[0]

        # breaking the remaining tie with the maximal P1-allowed sets (step 4)
        return _top_moves_by_set_count(tied_moves, Player2.get_maximal_allowed_sets(Color.P1, mini_board))[0]

    @staticmethod
    def get_miniboard(board: Board) -> Board | None:
        """
        Return a miniboard from the input board state. If there are multiple miniboards, this method can return any of them.

        The result keeps the full NUM_NODES x NUM_NODES shape, with every edge touching an excluded node set to
        Color.NONE. Returns None when no complete node set containing all colored edges has a P2-allowed move.
        """
        # collecting the nodes still on the board, and the ones that touch a colored edge
        active_nodes = [i for i in range(NUM_NODES) if any(c != Color.NONE for c in board[i])]
        colored_nodes = {
            i for i in active_nodes
            if any(c in (Color.P1, Color.P2) for c in board[i])
        }
        spare_nodes = [i for i in active_nodes if i not in colored_nodes]

        # growing the node set one size at a time, so the first valid set found is minimal
        # (any smaller valid set would already have been returned); the loop has to count upward
        for extra_size in range(len(spare_nodes) + 1):
            for added in combinations(spare_nodes, extra_size):
                node_set = colored_nodes | set(added)
                # skipping node sets that are missing an edge, since a miniboard must be complete
                if not _all_pairs_connected(board, node_set):
                    continue
                trimmed = _keep_only_nodes(board, node_set)
                if Player2.get_allowed_moves(Color.P2, trimmed):
                    return trimmed
        return None

    @staticmethod
    def get_maximal_allowed_sets(player: Color, board: Board) -> set[frozenset[Edge]]:
        """
        Return a set of all distinct maximal allowed sets for the given player over the input board state.
        If player is Color.P1, find all maximal p1-allowed sets; if player is Color.P2, find all maximal p2-allowed sets.

        "Maximal" means largest size (handout 2.3.1), not "cannot be extended". Edges are (i, j) with i < j.
        If the player has no allowed moves, the only allowed set is the empty one, so {frozenset()} is returned.
        """
        allowed = Player2.get_allowed_moves(player, board)
        taken_edges = _player_edges(player, board)

        largest_size = 0
        largest_sets: set[frozenset[Edge]] = set()
        current_set: list[Edge] = []

        # backtracking over subsets of `allowed`, adding moves only in increasing index order so
        # each subset is visited once; `current_set` and `taken_edges` are shared, so every
        # addition is undone right after the recursive call
        def explore_from(start_index: int) -> None:
            nonlocal largest_size, largest_sets
            # resetting the collection whenever a bigger set turns up
            if len(current_set) > largest_size:
                largest_size = len(current_set)
                largest_sets = set()
            if len(current_set) == largest_size:
                largest_sets.add(frozenset(current_set))
            # pruning branches that cannot even tie the largest size; this stays a strict `<`
            # because branches that can only tie still have to be explored
            if len(current_set) + len(allowed) - start_index < largest_size:
                return
            for idx in range(start_index, len(allowed)):
                move = allowed[idx]
                if not _makes_triangle(move, taken_edges):
                    current_set.append(move)
                    taken_edges.add(move)
                    explore_from(idx + 1)
                    taken_edges.remove(move)
                    current_set.pop()

        explore_from(0)
        return largest_sets

    @staticmethod
    def get_allowed_moves(player: Color, board: Board) -> list[Edge]:
        """
        Return a list of all distinct valid moves for the given player over the input board state.

        Only UNCOLORED edges are considered (NONE edges are not part of the board). Edges are (i, j) with i < j.
        """
        # checking every uncolored edge against the edges this player already owns
        taken_edges = _player_edges(player, board)
        return [
            (i, j)
            for i in range(NUM_NODES) for j in range(i + 1, NUM_NODES)
            if board[i][j] == Color.UNCOLORED and not _makes_triangle((i, j), taken_edges)
        ]


# Helpers. Edges inside `taken_edges` sets are always stored as (low, high).

def _player_edges(player: Color, board: Board) -> set[Edge]:
    """Return the edges already colored by `player`."""
    return {
        (i, j)
        for i in range(NUM_NODES) for j in range(i + 1, NUM_NODES)
        if board[i][j] == player
    }


def _makes_triangle(edge: Edge, taken_edges: set[Edge]) -> bool:
    """Return True if adding `edge` (either orientation) to the edges in `taken_edges` forms a triangle."""
    a, b = edge
    # looking for a third node already joined to both ends of the edge
    for k in range(NUM_NODES):
        if k != a and k != b and (min(a, k), max(a, k)) in taken_edges and (min(b, k), max(b, k)) in taken_edges:
            return True
    return False


def _all_pairs_connected(board: Board, node_set: set[int]) -> bool:
    """Return True if every pair of `node_set` is joined by an edge on `board`."""
    return all(board[i][j] != Color.NONE for i, j in combinations(sorted(node_set), 2))


def _keep_only_nodes(board: Board, node_set: set[int]) -> Board:
    """Return a copy of `board` with every edge touching a node outside `node_set` set to NONE."""
    return [
        [board[i][j] if i in node_set and j in node_set else Color.NONE for j in range(NUM_NODES)]
        for i in range(NUM_NODES)
    ]


def _top_moves_by_set_count(moves: list[Edge], move_sets: set[frozenset[Edge]]) -> list[Edge]:
    """
    Return every move from `moves` that appears in the greatest number of `move_sets`, in their original order.
    `moves` must be non-empty.
    """
    # counting how many sets each edge shows up in
    appearances = Counter(edge for s in move_sets for edge in s)
    top_count = max(appearances[m] for m in moves)
    return [m for m in moves if appearances[m] == top_count]
