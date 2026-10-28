from __future__ import annotations
from itertools import combinations
from consts import Board, Color, Edge, NUM_NODES


class GameBoard:
    """
    Game board manager class. Encapsulates behaviors concerning the state of the board.
    """

    def __init__(self) -> None:
        """
        Initialize `board` as the adjacency matrix for the starting board.
        Use `Color.NONE` for edges that do not exist, and `Color.UNCOLORED` for the other edges.
        """
        # building the matrix with no self-edges and every other edge uncolored
        self.board: Board = [
            [Color.NONE if row == col else Color.UNCOLORED for col in range(NUM_NODES)]
            for row in range(NUM_NODES)
        ]

    def color_edge(self, edge: Edge, color: Color) -> None:
        """
        Update `board` to reflect coloring the given edge.
        """
        # coloring both cells so (u, v) and (v, u) stay in sync
        u, v = edge
        self.board[u][v] = color
        self.board[v][u] = color

    def get_winner(self) -> Color | None:
        """
        Return the color of the player that has won (Color.P1 or Color.P2).
        If the game is still in progress (no one has won yet), return None.
        """
        # scanning every triangle for three edges of one player's color
        for x, y, z in combinations(range(NUM_NODES), 3):
            side = self.board[x][y]
            if side in (Color.P1, Color.P2) and self.board[x][z] == side and self.board[y][z] == side:
                # handing the win to the other player, since closing your own triangle loses
                return Color.P2 if side == Color.P1 else Color.P1
        return None

    def __str__(self) -> str:
        """
        Formats the board as a string. Provided for your convenience while debugging.
        """
        string = ""
        for row in self.board:
            for item in row:
                string += "{edge:<10}".format(edge=item.name)
            string += "\n"
        return string
