"""User inputs for chess-curator."""

filename = "teamlwseries_with_evals.pgn"
sample_games = True
sample_size = 100

sample_by_ids = False
sample_ids = ["Hz1RhCkq", "YhEA1DRr", "as8fHyLf", "IXeW8ATa", "JQUIIE3j",
              "gExDe6EN", "hYJCjfqW", "KahqBi5m", "mLPWaWIZ", "yOBN8AJz",
              "UeXwMphQ", "aQ1vWmyM", "iQaSjYxJ", "eYNgM9IG", "fbazCNgo",
              "2WcWpKfH", "lXQHli3B", "GGpwEOZG", "77OS03MG", "DCR0XTH2"]

sample_by_ids = False if sample_games else sample_by_ids
sample_games = False if sample_by_ids else sample_games
sample_size = 0 if not sample_games else sample_size
sample_ids = [] if not sample_by_ids else sample_ids



