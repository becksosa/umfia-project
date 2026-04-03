import re
import itertools
import pandas as pd
import numpy as np
import sys
sys.setrecursionlimit(200000)

target = 100
banked_scores = range(target)
opp_scores = range(target)
turn_scores = range(target)
players = ['p1', 'p2']

idx = pd.MultiIndex.from_product([players, banked_scores, opp_scores, turn_scores], names=[
                                 'player', 'my_score', 'opp_score', 'turn_score'])
df = pd.DataFrame(
    {'p_win_if_bank': None, 'p_win_if_roll': None}, index=idx).reset_index()


# Garunteed wins
df.loc[(df.my_score + df.turn_score >= target) & (df.my_score +
                                                  df.turn_score > df.opp_score) & (df.player == 'p2'), 'p_win_if_bank'] = 1
# print(df.loc[(df.my_score + df.turn_score > target) & (df.my_score + df.turn_score > df.opp_score)])


def optimal_p_win(player, my_score, opp_score, turn_score):
    # helper for the logic to account for differing odds per player
    next_player = 'p2' if player == 'p1' else 'p1'
    p_win_if_bank = df.loc[(df.player == player) &
                           (df.my_score == my_score) &
                           (df.opp_score == opp_score) &
                           (df.turn_score == turn_score),
                           'p_win_if_bank'].values[0]
    p_win_if_roll = df.loc[(df.player == player) &
                           (df.my_score == my_score) &
                           (df.opp_score == opp_score) &
                           (df.turn_score == turn_score),
                           'p_win_if_roll'] .values[0]

    if p_win_if_bank is not None and p_win_if_roll is not None:
        # Here, I return only the optimal value
        return max(p_win_if_roll, p_win_if_bank)

    p_bank_total = 0
    # logic for last chance round
    if player == 'p2' and opp_score >= target:
        # BANKING — game ends immediately
        p_bank_total = 1.0 if my_score + turn_score > opp_score else 0.0

        # ROLLING — separate last-chance roll loop
        p_roll_total = 0
        for d1, d2 in itertools.product(range(1, 7), range(1, 7)):
            if d1 == 1 and d2 == 1:
                p_roll_total += 0.0
            elif d1 == 1 or d2 == 1:
                p_roll_total += 0.0
            else:
                new_turn_score = turn_score + d1 + d2
                p_roll_total += optimal_p_win(player,
                                              my_score, opp_score, new_turn_score)

        p_win_if_roll = p_roll_total / 36

    else:
        p_roll_total = 0
        # handling dice rolls
        for d1, d2 in itertools.product(range(1, 7), range(1, 7)):
            if d1 == 1 and d2 == 1:  # SUPERSKUNK
                new_my_score = 0
                # Here, because it becomes the opponents turn, I am looking up 1 - their probability of winning
                p_roll_total += 1 - \
                    optimal_p_win(next_player, opp_score, new_my_score, 0)
            elif d1 == 1 or d2 == 1:  # SKUNK
                new_turn_score = 0
                # Same thing here
                p_roll_total += 1 - \
                    optimal_p_win(next_player, opp_score, my_score, 0)
            else:  # NORMAL ROLL
                new_turn_score = turn_score + d1 + d2
                # p of win for my optimal next choice
                p_roll_total += optimal_p_win(player,
                                              my_score, opp_score, new_turn_score)

        p_win_if_roll = p_roll_total / 36
        p_bank_total = 1 - \
            optimal_p_win(next_player, opp_score, my_score + turn_score, 0)

    df.loc[(df.player == player) & (df.my_score == my_score) & (df.opp_score == opp_score) & (df.turn_score == turn_score),
           'p_win_if_roll'] = p_win_if_roll

    df.loc[(df.player == player) & (df.my_score == my_score) & (df.opp_score == opp_score) & (df.turn_score == turn_score),
           'p_win_if_bank'] = p_bank_total

    return max(p_win_if_roll, p_bank_total)
