# QuizNerd

QuizNerd is a lightweight offline desktop quiz app built with Python, Tkinter, and SQLite.

It currently includes:

- a clean desktop home screen with `Solo` and `Multiplayer` modes
- a solo round with mixed multiple choice and true / false questions
- a multiplayer round with tap-to-reveal answers for quizmaster-style play
- a local question bank that seeds itself from `quiznerd_data.py`

## Stack

- Python
- Tkinter
- SQLite

No third-party Python packages are required.

## Run locally

Use either of these:

```bash
python3 quiznerd.py
```

Or double-click `Launch QuizNerd.command`.

## Test it

Run the basic checks:

```bash
python3 -m py_compile quiznerd.py quiznerd_data.py test_quiznerd.py
python3 -m unittest -v
```

## Project structure

- `quiznerd.py`: desktop UI and local database bootstrap
- `quiznerd_data.py`: built-in seed question bank
- `test_quiznerd.py`: lightweight tests for the local data layer
- `Launch QuizNerd.command`: double-click launcher for local use

## Data storage

- Running from source stores the local database in the project folder as `quiznerd.db`


## Notes for GitHub

This repo is set up to track source files only. Generated files such as the local database, app bundle, logs, and cache folders are ignored.
