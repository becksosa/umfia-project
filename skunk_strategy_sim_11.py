import random
import numpy as np
import pandas as pd
import math
from itertools import combinations
from sqlalchemy import create_engine
from io import StringIO
import csv
import time
import matplotlib.pyplot as plt

# ------------------
# MAIN GAME FUNCTIONS
# ------------------

engine = create_engine(
    "postgresql+psycopg2://sosa:1234@192.168.1.141:5432/skunk")


def bulk_insert(rows, table_name, engine, chunk_size=50000, max_retries=3):
    if not rows:
        return
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i+chunk_size]
        conn = None
        for attempt in range(max_retries):
            try:
                output = StringIO()
                writer = csv.DictWriter(
                    output, fieldnames=chunk[0].keys(), delimiter='\t')
                writer.writerows(chunk)
                output.seek(0)
                conn = engine.raw_connection()  # direct assign, no context manager
                with conn.cursor() as cur:
                    cur.copy_from(output, table_name, null='',
                                  columns=list(chunk[0].keys()))
                conn.commit()
                if i % (chunk_size * 10) == 0:
                    print(
                        f'  inserting {len(rows)} rows into {table_name}...')
                break
            except Exception as e:
                print(f'  insert attempt {attempt+1} failed: {e}')
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
            finally:
                if conn:
                    conn.close()


def take_turn(scores, strategies, me, opponent, is_last_chance_round):
    turn_report = []
    roll_count = 0
    turn_score = 0
    superskunk = False

    while True:
        state = {"bot_score_before_turn": int(scores[me]),
                 "opponent_score_before_turn": int(scores[opponent]),
                 "roll_count": roll_count,
                 "turn_score": turn_score,
                 "is_last_chance_round": is_last_chance_round}

        roll_decision = strategies[me](state)
        if not roll_decision:
            turn_report.append(
                {**state, "roll_decision": False, "die_one": None, "die_two": None})
            break

        die_one, die_two = random.randint(1, 6), random.randint(1, 6)
        roll_count += 1

        if die_one == 1 and die_two == 1:
            superskunk = True
            turn_score = 0
            turn_report.append(
                {**state, "roll_decision": True, "die_one": die_one, "die_two": die_two})
            break
        elif die_one == 1 or die_two == 1:
            turn_score = 0
            turn_report.append(
                {**state, "roll_decision": True, "die_one": die_one, "die_two": die_two})
            break
        else:
            turn_score += (die_one + die_two)
            turn_report.append(
                {**state, "roll_decision": True, "die_one": die_one, "die_two": die_two})

    return turn_score, turn_report, superskunk


def simulate_game(bot_1, bot_2, game_id=1):
    scores = {bot_1["name"]: 0, bot_2["name"]: 0}
    strategies = {bot_1["name"]: bot_1["strategy"],
                  bot_2["name"]: bot_2["strategy"]}
    players = [bot_1["name"], bot_2["name"]]
    is_last_chance_round = False
    game_report = []
    target = 100
    turn_id = 1

    # print(scoreboard)
    # Loop for one round that ends when target is reached (with last chance round for p2)
    while True:
        if turn_id == 100000:
            print("WARNING - infinite loop")
            break  # you're missing this
        # Player 1
        me, opponent = players[0], players[1]
        turn_score, turn_report, superskunk = take_turn(
            scores, strategies, me, opponent, is_last_chance_round)
        scores[me] = 0 if superskunk else scores[me] + turn_score
        for row in turn_report:
            row["player"] = me
            row["turn_id"] = turn_id
        game_report.extend(turn_report)
        if scores[me] >= target:
            is_last_chance_round = True
        turn_id += 1

        # Player 2
        me, opponent = players[1], players[0]
        turn_score, turn_report, superskunk = take_turn(
            scores, strategies, me, opponent, is_last_chance_round)
        scores[me] = 0 if superskunk else scores[me] + turn_score
        for row in turn_report:
            row["player"] = me
            row["turn_id"] = turn_id
        game_report.extend(turn_report)
        turn_id += 1

        if is_last_chance_round or scores[players[1]] >= target:
            if scores[players[0]] > scores[players[1]]:
                winner = players[0]
                bot_1["wins"] += 1
                bot_2["losses"] += 1
            elif scores[players[1]] > scores[players[0]]:
                winner = players[1]
                bot_2["wins"] += 1
                bot_1["losses"] += 1
            else:
                winner = "tie"

            for row in game_report:
                row["winner"] = winner
                row["game_id"] = game_id
            break
    return game_report


def simulate_games(bot_1, bot_2, games_to_simulate, matchup_id):
    matchup_report = []
    bot_1_game_wins = 0
    bot_2_game_wins = 0
    for game in range(games_to_simulate):
        game_report = simulate_game(bot_1, bot_2, game_id=game+1)
        matchup_report.extend(game_report)
        # last row of game_report has the winner
        winner = game_report[-1]["winner"]
        if winner == bot_1["name"]:
            bot_1_game_wins += 1
        elif winner == bot_2["name"]:
            bot_2_game_wins += 1
    for row in matchup_report:
        row["matchup_id"] = matchup_id
    # increment match_wins on the winner
    if bot_1_game_wins > bot_2_game_wins and "match_wins" in bot_1:
        bot_1["match_wins"] += 1
    elif bot_2_game_wins > bot_1_game_wins and "match_wins" in bot_2:
        bot_2["match_wins"] += 1
    return matchup_report


def round_robin_simulation(population, games_per_matchup, evolution_sim, generation):
    matchup_id = 1
    buffer = []
    total_matchups = math.comb(len(population), 2)
    for bot_1, bot_2 in combinations(population, 2):
        matchup_report = simulate_games(
            bot_1, bot_2, games_per_matchup, matchup_id)
        for row in matchup_report:
            row["simulation_id"] = generation
            row["evolution_sim"] = evolution_sim
        buffer.extend(matchup_report)
        if matchup_id % 100 == 0:  # flush
            bulk_insert(buffer, "rolls", engine)
            buffer.clear()
            print(
                f'Matchup {matchup_id} of {total_matchups} complete, buffer flushed')
        matchup_id += 1
    if buffer:
        bulk_insert(buffer, "rolls", engine)


def paramaterized_heuristic_bot(state, target_score, desperation_intensity, comfort_intensity):
    p_superskunk = 1/36
    p_skunk = 10/36
    p_safe = 25/36
    ev_safe_roll = 8
    gap = (state["bot_score_before_turn"] + state["turn_score"]) - \
        state["opponent_score_before_turn"]  # new variable for paramaterized bot
    outcome_stop = state["bot_score_before_turn"] + state["turn_score"]
    outcome_safe = state["bot_score_before_turn"] + \
        state["turn_score"] + ev_safe_roll
    outcome_skunk = state["bot_score_before_turn"] + 0
    outcome_superskunk = 0
    ev_one_more_roll = (p_safe * outcome_safe) + (p_skunk *
                                                  outcome_skunk) + (p_superskunk * outcome_superskunk)

    # Parameters
    # Hard checks
    if state["turn_score"] >= target_score:
        return False
    elif state["is_last_chance_round"] and (state["bot_score_before_turn"] + state["turn_score"]) < state["opponent_score_before_turn"]:
        return True

    # Multipliers
    if gap < 0:  # playing from behind
        multiplier = desperation_intensity ** abs(gap)
        ev_one_more_roll *= multiplier

    elif gap > 0:  # playing from ahead
        multiplier = comfort_intensity ** gap
        ev_one_more_roll *= 1 / multiplier

    # Final logic
    if outcome_stop < ev_one_more_roll:
        return True
    else:
        return False


gen_1_population = []
for i in range(40):
    params = {
        "target_score": random.randint(10, 60),
        "desperation_intensity": random.uniform(1, 3),
        "comfort_intensity": random.uniform(1, 3)}
    bot = {
        "generation": 0,
        "id": f"0.{i}",
        "name": f"bot_0.{i}",
        ** params,
        "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    gen_1_population.append(bot)


# this one doesn't need to be able to take params, just added as some extra diversification
def randomly_random_bot():
    bot = {
        "generation": "randomly_random",
        "id": "randomly_random",
        "name": f"randomly_random_bot",
        "strategy": lambda state: random.random() < random.uniform(0.1, 0.9),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    return bot
# print(randomly_random_bot(None))


def cautious_bot():
    params = {
        "target_score": random.randint(10, 20),
        "desperation_intensity": 1.0,
        "comfort_intensity": random.uniform(1.5, 2.5)}
    bot = {
        "generation": "cautious",
        "id": "cautious",
        "name": "cautious_bot",
        **params,
        "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    return bot
# print(cautious_bot(None))


def risky_bot():
    params = {
        "target_score": random.randint(30, 50),
        "desperation_intensity": random.uniform(1.5, 2.5),
        "comfort_intensity": 1.0}
    bot = {
        "generation": "risky",
        "id": "risky",
        "name": "risky_bot",
        **params,
        "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    return bot


def desperate_bot():
    params = {
        "target_score": random.randint(0, 10),
        "desperation_intensity": random.uniform(1.5, 2.5),
        "comfort_intensity": 1, }
    bot = {
        "generation": "desperate_bot",
        "id": "desperate_bot",
        "name": "desperate_bot",
        **params,
        "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    return bot


def comfortable_bot():
    params = {
        "target_score": random.randint(0, 10),
        "desperation_intensity": 1,
        "comfort_intensity": random.uniform(1.5, 2.5)}
    bot = {
        "generation": "comfortable_bot",
        "id": "comfortable_bot",
        "name": "comfortable_bot",
        **params,
        "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    return bot


def roll_counter_bot():
    params = {
        "target_score": random.randint(0, 20),
        "desperation_intensity": 1.0,
        "comfort_intensity": 1.0}
    bot = {
        "generation": "roll_counter",
        "id": "roll_counter",
        "name": "roll_counter_bot",
        **params,
        "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
        "wins": 0,
        "losses": 0,
        "match_wins": 0}
    return bot


diverse_population = [randomly_random_bot, cautious_bot,
                      risky_bot, desperate_bot, comfortable_bot, roll_counter_bot]


def mutate(survivors, number_mutants, generation):
    mutants = []
    # only paramaterized bots can be parents
    eligibile_parents = [bot for bot in survivors if "target_score" in bot]
    while len(mutants) < number_mutants:

        parent = random.choice(eligibile_parents)
        params = {
            "target_score": max(0, parent["target_score"] + random.randint(-5, 5)),
            "desperation_intensity": max(1, parent["desperation_intensity"] + random.uniform(-0.15, 0.15)),
            "comfort_intensity": max(1, parent["comfort_intensity"] + random.uniform(-0.15, 0.15))}
        bot = {
            "generation": generation,
            "id": f"{parent['id']}.mut.{generation}.{len(mutants)}",
            "name": f"{parent['name']}_mutant_{generation}.{len(mutants)}",
            ** params,
            "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
            "wins": 0,
            "losses": 0,
            "match_wins": 0}
        mutants.append(bot)
    return mutants


def crossbreed(survivors, number_crossbreeds, generation):
    crossbreeds = []
    eligible_parents = [bot for bot in survivors if "target_score" in bot]
    while len(crossbreeds) < number_crossbreeds:
        parent_a, parent_b = random.sample(eligible_parents, 2)
        params = {
            "target_score": random.choice([parent_a["target_score"], parent_b["target_score"]]),
            "desperation_intensity": random.choice([parent_a["desperation_intensity"], parent_b["desperation_intensity"]]),
            "comfort_intensity": random.choice([parent_a["comfort_intensity"], parent_b["comfort_intensity"]])}
        bot = {
            "generation": generation,
            "id": f"{parent_a['id']}+{parent_b['id']}.{generation}.{len(crossbreeds)}",
            "name": f"crossbreed_{generation}.{len(crossbreeds)}",
            **params,
            "strategy": lambda state, p=params: paramaterized_heuristic_bot(state, **p),
            "wins": 0,
            "losses": 0,
            "match_wins": 0}
        crossbreeds.append(bot)
    return crossbreeds


# just to add counter for next sim to be dtagged in SQL db correctly


def evolution(pop_dict, num_mutants, num_immigrants, num_diverse, num_crossbreed, generations, games_per_matchup):
    '''
    Starting pop is 20 bots from the first sim, the winners from our first simulation
    mutant_pop = # of mutants per generation
    diverse_pop = # of diverse bots per generation
    num_immigrants = # of completely new random gen paramaterized bots per generation
    '''
    global full_sim_attempts
    # adding a counter to differentiate my attempts to do the evolutionary sim in db
    full_sim_attempts += 1
    # Mutation and diversification:
    print(f'''Starting evolutionary sequence with:
   - {len(pop_dict)} survivors per generation
   - {num_mutants} mutants per generation
   - {num_crossbreed} crossbreds per generation
   - {num_immigrants} new randomized paramaterized bots per generation
   - {num_diverse} randomly selected diverse bots per generation\n''')
    pop = pop_dict.copy()  # Can get rid of this later (maybe)
    generation = 1

    while generation <= generations:
        print('*' * 40)
        print(f'\nBeginning generation {generation} simulation...\n')

        for bot in pop:
            bot["match_wins"] = 0

        mutants = mutate(pop, num_mutants, generation)
        crossbreeds = crossbreed(pop, num_crossbreed, generation)
        pop.extend(mutants)
        pop.extend(crossbreeds)

        for i in range(num_immigrants):
            immigrant_params = {
                "target_score": random.randint(10, 60),
                "desperation_intensity": random.uniform(1, 3),
                "comfort_intensity": random.uniform(1, 3)}
            immigrant_bot = {
                "generation": generation,
                "id": f"{generation}.{i}",
                "name": f"bot_{generation}.{i}",
                ** immigrant_params,
                "strategy": lambda state, p=immigrant_params: paramaterized_heuristic_bot(state, **p),
                "wins": 0,
                "losses": 0,
                "match_wins": 0}
            pop.append(immigrant_bot)

        for i in range(num_diverse):
            diverse_bot = random.choice(diverse_population)()
            diverse_bot["name"] = f"diverse_bot_{generation}.{i}"
            pop.append(diverse_bot)

        pop_df = pd.DataFrame(pop)
        pop_df["evolution_sim"] = full_sim_attempts  # evolution column
        pop_df.drop(columns=["strategy"]).to_sql(
            "bots", con=engine, if_exists="append", index=False)
        print(f'population report added to sql database')
        # note duplicates will need to be handled in SQL db

        # Run simulation and kill off the bottom half of the population\
        round_robin_simulation(pop, games_per_matchup,
                               full_sim_attempts, generation)
        print(f'\nsimulation report added to sql database')

        print(f"calculating winners...")

        leaderboard_df = pd.DataFrame([
            {"winner": bot["name"], "match_wins": bot.get(
                "match_wins", 0), "game_wins": bot.get("wins", 0)}
            for bot in pop
        ]).sort_values("match_wins", ascending=False) \
            .reset_index(drop=True) \
            .assign(generation=generation, evolution_sim=full_sim_attempts)

        leaderboard_df.to_sql("leaderboards", con=engine,
                              if_exists="append", index=False)
        print(f'leaderboard report added to sql database')
        cull_size = int(len(pop) * 0.4)
        survivors = leaderboard_df.nlargest(cull_size, "match_wins")[
            "winner"].tolist()
        pop = [bot for bot in pop if bot["name"] in survivors]
        print(
            f'The losers have been slaughtered. Population reduced to {len(pop)} bots.\n')
        generation += 1
    print(f"Evolution complete!\n")


full_sim_attempts = 10
evolution(gen_1_population, 30, 14, 8, 8,
          generations=100, games_per_matchup=200)
