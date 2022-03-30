# chess-curator

Assorted scripts that can identify interesting things about chess games, such as:

- Trying to identify piece sacrifices (detect_sacs.py)
- Identifying games that ended in well-known checkmate patterns (detect_mates.py)
- Stats about seven-piece tablebase positions that were reached (TBC)
- Stats about different endgames that were reached (TBC)
- Stats about tactics

All scripts are designed to only work with PGNs containing games played on Lichess. Some scripts require the input PGN to include eval data; others don't. Using non-Lichess PGNs is sure to raise an error or three early on.

