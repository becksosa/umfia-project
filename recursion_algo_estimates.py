import itertools
import csv

target = 100
memo = {}


def get_optimal(player, my_score, opp_score, turn_score):
    """Lookup with edge case handling for states outside memo."""
    k = (player, my_score, opp_score, turn_score)
    if k in memo:
        return max(memo[k])

    # Game over — P2 already won
    if player == 'p1' and opp_score >= target:
        return 0.0

    # P2 last chance — can bank to beat opponent?
    if player == 'p2' and opp_score >= target:
        return 1.0 if my_score + turn_score > opp_score else 0.0

    # Normal play — banking reaches target
    if my_score + turn_score >= target:
        return 1.0

    return 0.5  # safety fallback, shouldn't be hit


def compute_state(player, my_score, opp_score, turn_score):
    next_player = 'p2' if player == 'p1' else 'p1'

    # P2 last chance round
    if player == 'p2' and opp_score >= target:
        p_bank = 1.0 if my_score + turn_score > opp_score else 0.0

        p_roll_total = 0
        for d1, d2 in itertools.product(range(1, 7), range(1, 7)):
            if d1 == 1 and d2 == 1:
                p_roll_total += 0.0
            elif d1 == 1 or d2 == 1:
                p_roll_total += 0.0
            else:
                p_roll_total += get_optimal(player, my_score,
                                            opp_score, turn_score + d1 + d2)
        p_roll = p_roll_total / 36

    # Normal play
    else:
        p_roll_total = 0
        for d1, d2 in itertools.product(range(1, 7), range(1, 7)):
            if d1 == 1 and d2 == 1:
                p_roll_total += 1 - get_optimal(next_player, opp_score, 0, 0)
            elif d1 == 1 or d2 == 1:
                p_roll_total += 1 - \
                    get_optimal(next_player, opp_score, my_score, 0)
            else:
                p_roll_total += get_optimal(player, my_score,
                                            opp_score, turn_score + d1 + d2)
        p_roll = p_roll_total / 36
        p_bank = 1 - get_optimal(next_player, opp_score,
                                 my_score + turn_score, 0)

    return (p_roll, p_bank)


# Build state space — only states that need computation
all_keys = []

# P1 and P2 normal play: scores 0-99, turn_score only up to what matters
for player in ['p1', 'p2']:
    for my_score in range(target):
        for opp_score in range(target):
            for turn_score in range(target - my_score):
                all_keys.append((player, my_score, opp_score, turn_score))

# P2 last-chance: opp already hit target, P2 needs to catch up
for my_score in range(target):
    for opp_score in range(target, target + 20):
        for turn_score in range(opp_score - my_score + 1):
            all_keys.append(('p2', my_score, opp_score, turn_score))

# Initialize all with a guess
for key in all_keys:
    memo[key] = (0.5, 0.5)

print(f"Total states: {len(all_keys)}")

# Value iteration
for iteration in range(200):
    max_change = 0
    for key in all_keys:
        player, my_score, opp_score, turn_score = key
        old_val = max(memo[key])
        new_roll, new_bank = compute_state(
            player, my_score, opp_score, turn_score)
        memo[key] = (new_roll, new_bank)
        max_change = max(max_change, abs(max(new_roll, new_bank) - old_val))

    print(f"Iteration {iteration}, max change: {max_change}")
    if max_change < 1e-6:
        print("Converged!")
        break

# Dump to CSV
with open('skunk_optimal.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['player', 'my_score', 'opp_score',
                    'turn_score', 'p_win_if_roll', 'p_win_if_bank'])
    for key, (p_roll, p_bank) in memo.items():
        writer.writerow([*key, p_roll, p_bank])

print(f"Saved {len(memo)} states to skunk_optimal.csv")
