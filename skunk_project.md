# Skunk Project

There are several variations of a dice game called SKUNK, a game that involves chance,
decision making and probability. You are being asked to build an algorithm or heuristic to
play this game. The rules are as follows:

There can be as few as 2 players and as many as N players.
The first player rolls a pair of dice and accumulates the total score until the player either
rolls a 1 on one of the two dice, or two 1s on both dice (“snake eyes” or “skunk”), or decides
to call “stop” and collect the accumulated total. If the player ends up rolling a single 1 on
one of the two dice, that player’s turn ends and collects no points for that round. If the
player rolls double 1s (“snake eyes” or “skunk”), the player’s turn ends and loses all
accumulated points up to this point in the game for all played rounds and their
accumulated total goes to zero. The player can continue to roll as many times as they want
to accumulate points during their turn. They just risk rolling a 1 or double 1s and ending
their turn.

The play ends when a player gets to a total target agreed to at the beginning of the game,
typically 100 points. However, if a given player gets to the target, any other players who
have not yet had a chance to play that round get one more turn, so that all players have the
same number of turns at the end of the game.

Write a computer function in a programming language of your choice that takes as input 1)
the target total points, 2) a vector of points accumulated by you and other players up to this
point, and 3) your order in the number of players (for example, you might be player #2 out of
4 players. This matters if player #1 gets to the total first, and you only have one more turn
left to catch up). The computer function should determine the logic for rolling or stopping
to bank accumulated points. Generate a random roll of two dice in this function if you
choose to roll. If you get a single 1, your turn ends and you get zero points. If you get two
1s, you lose all points accumulated up to this point and your turn ends. If you don’t get any
1s, you accumulate those points and you can choose to stop or keep rolling. When your
turn ends, update the vector with your new total.

Be prepared to explain the logic of your function to play this dice game. Think about
discussing the following questions in an interview:

 - Is there an optimal way to play this game?
- Does the risk preference of your algorithm matter and should it be consistent
throughout the rounds of play?
- If you believe there is an optimal way to play, do you think there is a solution to
determine your probability of winning? Would it depend on how other players play
their game?
 - How would you consider writing a program to test out multiple skunk-bots with
different logic playing against one another? Could you write a skunk-bot that
improves its logic dynamically depending on its historical performance?
-----------
------------
---------------------
Notes:
 - throughout this project I refer to the different types of rolls like so:
 - superskunk = snake eyes, lose all your points
 - skunk = dice roll includes a 1, lose all points for that turn

The project prompt asks to design a heuristic, I started with a heuristic of a "target score" but then developed a technique that I thought was better using probability and the expected value of choosing to roll or not. That is what is described below:

--------

# Is There an Optimal Way to Play This Game?

My first thought was to simply use probability to calculate the expected value of the outcome of rolling the dice, and only roll when the expected value of the outcome was greater than the expected value of not rolling. I based this calculation on the "state" of the game. An example is included below:
``` python
# Example state
test_state = {"bot_score_before_turn": 69,
        "opponent_score_before_turn": 52,
        "roll_count": 12,
        "turn_score": 5,
        "is_last_chance_round": False}
```
To make my calculation I defined the probability of each outcome, and then used the variables in the state to calculate the expected outcome of making each decision. The "expected outcome" is a probabilistic representation of the players total score after rolling (or not rolling) the dice.

```python
# Probabilities of possible rolls:
p_superskunk = 1/36
p_skunk = 10/36
p_safe = 25/36

# To find the average value of one roll I took the sum of all dice rolls without 1s and divided by the probability of getting a safe roll 
dice = np.arange(2, 7)
dice_df = pd.DataFrame(
    np.add.outer(dice, dice),
    index=dice,
    columns=dice
)
ev_safe_roll = dice_df.to_numpy().sum() / 25

# Possible outcomes
outcome_stop = test_state["bot_score_before_turn"] + test_state["turn_score"]
outcome_safe = test_state["bot_score_before_turn"] + test_state["turn_score"] + ev_safe_roll
outcome_skunk = test_state["bot_score_before_turn"] + 0
outcome_superskunk = 0

# Calculating the expected value of one more roll
ev_one_more_roll = (p_safe * outcome_safe) + (p_skunk * outcome_skunk) + (p_superskunk * outcome_superskunk)
print(f'The expected total points of the bot after rolling again is {round((ev_one_more_roll),2)} points')
``` 
Output:
```
The expected total points of the bot after rolling again is 76.11 points
```
Based on the example state, the bot would choose to roll because the expected outcome is a total of 76.11 points, which is more than the points the bot would have if it stopped (69 + 5 points). I've included an example of one of the bots I created below, and it's output given the variables from the "state" dictionary above:

-----------------------------

### The Bot to Use My Strategy:
```python
def paramaterized_heuristic_bot(state, target_score, desperation_intensity, comfort_intensity):
    p_superskunk = 1/36
    p_skunk = 10/36
    p_safe = 25/36
    ev_safe_roll = 8
    outcome_stop = state["bot_score_before_turn"] + state["turn_score"]
    outcome_safe = state["bot_score_before_turn"] + \
        state["turn_score"] + ev_safe_roll
    outcome_skunk = state["bot_score_before_turn"] + 0
    outcome_superskunk = 0
    ev_one_more_roll = (p_safe * outcome_safe) + (p_skunk *
                                                  outcome_skunk) + (p_superskunk * outcome_superskunk)

    if outcome_stop < ev_one_more_roll:
        return True
    else:
        return False
    
test_bot_output = paramaterized_heuristic_bot(test_state, 1000, 1, 1)
print(test_bot_output)
```
Output:
```
True
```
Based on the sample state, the bot returned True, meaning it would roll again in this situation.

## Benchmarking the Bot
The math made sense, but I needed proof. I had my bot play 10,000 games against a bot that chose with no strategy, purely random. Note that I did not include the majority of my game functions in this file because they would take up too much space. If you want to view them they are in [this Jupyter notebook](/skunk_project.ipynb). 

Note: the bots are defined as dictionaries designed to be used in a very large evolutionary simulation, I will get to this part later (spoiler - I spent a really long time on it and it did not end up being my final strategy).

#### Random Bot vs A Bot Maximizing Expected Value of Every Roll:
```python
random_bot = {
    "generation": "random",
    "id": "random",
    "name": f"random_bot",
    "strategy": lambda state: random.choice([True, False]),
    "wins": 0,
    "losses": 0,
    "match_wins": 0}

ev_bot = {
    "generation": "ev_bot",
    "id": "ev_bot",
    "name": "ev_bot",
    "strategy": lambda state: paramaterized_heuristic_bot(state),
    "wins": 0,
    "losses": 0,
    "match_wins": 0}

# Simulate 10,000 games and generate a post game summary
random_vs_ev = simulate_games(ev_bot, random_bot, 10000, 1)
random_vs_ev_df = pd.DataFrame(random_vs_ev)
wins = random_vs_ev_df.groupby("game_id")["winner"].first().value_counts()
print(wins)
```
Output:
```python
winner
ev_bot        8955
random_bot    1040
tie              5
```


# My Evolutionary Algorithm
I spent a lot of time working on creating an evolutionary algorithm. My strategy was to create parameterized bots that still made decisions based on the expected value model I made, but had adjustable parameters. In my final simulation I ended up going with:
 - Target score (the original heuristic)
 - Desperation intensity - a multiplier to make bots get more aggressive when losing
 - Comfort intensity - a multiplier to make bots more conservative when winning

In my final attempt at the simulation, the population for every generation was made up of:
 - 40 survivors
 - 30 bots mutated from the survivors of the previous generation by taking the parameters and giving them slight random adjustments
 - 14 completely new bots with randomly generated parameters
 - 8 bots that were crossbred from the surviving population by taking some parameters from two different parent survivors
 - 8 diverse bots randomly selected from a population with different strategies like counting to a specific number of rolls, completely random decisions, extreme caution or risktaking, etc.


Unfortunately, my evolutionary process just wasn't feasible on the hardware I have. I kept running into crashes from RAM overloading, or running out of disk space because I was trying to record every single roll into a SQL database I was hosting on my LAN on a separate computer.

I'm moderately confident it would work if I had the hardware to run the simulation with a larger population size and more generations. Perhaps in hindsight I should have used fewer parameters so that the algorithm did not need to explore such a large combination of parameters. Either way it was a great learning experience - I included [the python script](/skunk_strategy_sim_11.py) in the repo just in case you want to take a look at it. 

# My Next Strategy - Probability Table Lookup
After spending too long on my evolutionary algorithm, my next strategy was inspired by this question: 

 - If you believe there is an optimal way to play, __do you think there is a solution to
determine your probability of winning__? Would it depend on how other players play
their game?

My next strategy was to take every single possible game state and calculate:
 - Probability of winning if rolling the dice is chosen
 - Probability of winning if banking the points is chosen

 Then, instead of a bot that makes its choice based on maximizing the expected value of a **single** roll. I can make a bot that also takes into account the opponent's score, and chooses the option that has a **higher probability of winning** every single time. The first step was to make a table with:
 - **player** - I thought this was important to specify because player 1 and player 2 don't necessarily have the same odds. If player 1 hits 100 first player 2 still has a chance, if player 2 hits 100 first player 1 doesn't get another chance. Probably a marginal difference in probability, but still worth capturing.
 - **my_score** - current score of the bot
 - **opp_score** - opponent's current score
 - **turn_score** - current accumulated score of the turn, the amount put at risk by rolling
 - **p_win_if_bank** - the probability of winning if the bot chooses to bank the turns points
 - **p_win_if_roll** - the probability of winning if the bot chooses to roll again
```python
idx = pd.MultiIndex.from_product([players, banked_scores, opp_scores, turn_scores], names=[
                                 'player', 'my_score', 'opp_score', 'turn_score'])
df = pd.DataFrame(
    {'p_win_if_bank': None, 'p_win_if_roll': None}, index=idx).reset_index()
```
The table:

![Unfilled probability table](/assets/unfilled_prob_table.png)

That was the easy part. Now I needed to fill in 2,000,000 rows of probabilities. I started with the ones I knew for certain:
``` python
# Guaranteed wins
# When the bot is player 2 and its total score is greater than the target, and the opponent's score
df.loc[(df.my_score + df.turn_score >= target) & (df.my_score + df.turn_score > df.opp_score) & (df.player == 'p2'), 'p_win_if_bank'] = 1
# This only applies to player 2 because if player 1 hits 100 points player 2 still has a chance
```
Next I wrote a function to return the optimal choice based on the table (the greater of p_win_if_roll and p_win_if_bank). However, I only have the probabilities of a select few game states, but that could be solved using a recursive function. If I call the function and the probabilities of the given game state are *not* already in the lookup, all 36 possible dice rolls are calculated and the new game states are calculated based on these dice rolls.

Then the function is called again with the new game states, and the process repeats itself like this again, and again, and again and again until eventually a game state that *does have probabilities in the lookup table* is reached (This being the guaranteed wins from above). Using these probabilities, the probabilities of the the game state that led to the current state are calculated, and then the ones that led to that one, and so on and the entire table fills itself in all at once.
 - I've included an AI generated visual representation of the process [here](https://becksosa.github.io/umfia-project/recursive_example.html). 

```python
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
    
    # Here, I return the optimal value if the probability is in the table, or continue to calculation if not
    if p_win_if_bank is not None and p_win_if_roll is not None:

        return max(p_win_if_roll, p_win_if_bank)

    p_bank_total = 0
    # logic for last chance round
    if player == 'p2' and opp_score >= target:
        # Bbanking — game ends immediately
        p_bank_total = 1.0 if my_score + turn_score > opp_score else 0.0

        # Rolling — separate last-chance roll loop
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
                # Here, because it becomes the opponent's turn, I am looking up 1 - their probability of winning
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
```

Unfortunately, I was once again limited by my hardware. In hindsight, I should have used a dictionary instead of a pandas DataFrame. This would have had less overhead, but it probably still wouldn't have made a difference because the amount of recursive function calls was so huge.

Still, I knew that my logic was good and this wasn't a problem that couldn't be solved. I consulted with my assistant (Claude), and showed it my function, asking how I could make it work on my hardware. It helped me draw up [this new function](/recursion_algo_estimates.py). It was the same basic idea but instead of using recursive functions, each value in the table started at a probability of .5. Each time the function loops a correct probability is calculated and added to the table, starting with the guaranteed wins. As the function iterates over and over the accurate probabilities cascade down and the probabilities below them that started at .5 make a "reasonable guess" as to what the probability should be. Eventually after many iterations, the probabilities are materially accurate. 

I ran the function, choosing to let it end when 200 iterations had been reached, or when the maximum cascading adjustment was less than 1e-6. It took about an hour and ~130 iterations to reach this point, slow but still much faster than my evolutionary algorithm (and I only needed to do it once). I uploaded it to my SQL server and did a few quick checks to see if the numbers looked reasonable. They did.

![Skunk Prob Table](/assets/sql_skunk_prob_table.png)

## The Final Bot
So, I made the bot that always chose the decision which gave it the highest probability to win:
```python
def prob_table_strat(state):
    # game function does not return a player variable but I know which I am based on placement, have to change manually
    player = 'p1'
    my_score = state["bot_score_before_turn"]
    opp_score = state["opponent_score_before_turn"]
    turn_score = state["turn_score"]

    # bank if winning:
    if my_score + turn_score >= 100:
        return False
    
    row = lookup[('p1', my_score, opp_score, turn_score)]
    p_win_if_roll = row['p_win_if_roll']
    p_win_if_bank = row['p_win_if_bank']
    if p_win_if_roll >p_win_if_bank:
        return True
    else:
        return False

prob_table_bot = {
    "generation": "prob_table_bot",
    "id": "prob_table_bot",
    "name": "prob_table_bot",
    "strategy": prob_table_strat,
    "wins": 0,
    "losses": 0,
    "match_wins": 0}
```
To put it to the test, I gave it an opponent which had previously performed quite well. My bot that always chose the option with the highest expected value:
```python
# Simulate 10,000 games and generate a post game summary
ev_vs_prob_table = simulate_games(prob_table_bot, ev_bot, 10000, 1)
ev_vs_prob_table_df = pd.DataFrame(ev_vs_prob_table)
wins = ev_vs_prob_table_df.groupby("game_id")["winner"].first().value_counts()
print(wins)
```
```
winner
prob_table_bot    5537
ev_bot            4428
tie                 35
```
I ran the simulation a few times and my new bot consistently won ~55% of the games. A small increase, but an increase nevertheless. The only real edge my new bot has against the old one is that it plays situationally, which is an advantage, but in a game with a lot of luck there's only so much you can do in any situation to beat an opponent that always makes a choice that will (probabilistically) maximize their score.

I made a few charts to compare the strategies:

![Bot comparison charts](/assets/bot_comparison_charts.png)

Notable observations:
 - The **turn score distribution when stopping** histogram clearly reflects the probability table bot's situational strategy. The expected value bot has a much smaller range of stopping points because it does not consider the point deficit when making decisions.
 - The **roll rate by score differential** chart clearly highlights the probability table bot's situational awareness. At larger deficits it is more likely to roll. With a larger lead, it is less likely to roll.
 - The probability table bot had a significantly higher roll rate on turns with a higher roll count. Although it should be considered that as the roll count gets higher, the density of data points decreases because each roll introduces a 10/36 chance of skunking.
 - In general, the probability table bot was more likely to roll as total turn score increased than the expected value bot. This is subject to the same scrutiny as above.

The probability table bot is exactly what I hoped to create with my evolutionary algorithm. I would have expected my "desperation" and "comfort" parameters to converge towards a meaningful result that would allow the bot to play situationally based on the score gap, just like the probability table bot does.

# Conclusion
There is an optimal way to play this game, and it's to consider probability at every turn. A strategy that's impossible for a real human without the help of programming. I feel confident that my bot would win a majority of games against a real human.

The risk preference of the algorithm absolutely matters, as is evidenced by my probability table bot vs expected value bot. When at a deficit, a player should increase their risk preference. When playing with a lead, a player should have a lower risk preference.

There is a solution to determine the probability of winning, at any given point. See my [probability table](/skunk_optimal.csv).

To write a program to test out multiple skunk bots I would do it like how I did it in [this python script](/skunk_strategy_sim_11.py). That being said, I wouldn't do it because as I discovered there is a much faster way to make a bot that *always* makes the best decision.


#### Final Note

My original plan was to start with the two player strategy and then move on to N players, but I ran out of time because I spent so long trying to force my evolutionary algorithm to work without it taking 12 hours to run a simulation.

That being said, my EV bot strategy would certainly work in a game with N players, as it does not take any input of opponent's score regardless. My probability table strategy would also certainly work, but the size of the probability table would increase dramatically by adding even one more player.
