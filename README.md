# Sim (Programming Assignment #4)

`sim_board.py` holds the `GameBoard`, and `player2.py` holds the `Player2` strategy bot. `game.py` is the provided turtle GUI.

Run the tests from this folder:

```
python -m pytest
```

Use `python -m pytest`, not a bare `pytest`. The `-m` form puts this folder on the import path, which the tests need for `from consts import ...`.
