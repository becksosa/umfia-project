import random


# DICE ROLL:
def dice_roll():
    return [random.randint(1, 6), random.randint(1, 6)]


# GET USER INPUT (YES/NO):
def yes_or_no(prompt):
    while True:
        answer = input(prompt + " (yes/no): ").strip().lower()
        if answer in ("yes", "y"):
            return True
        elif answer in ("no", "n"):
            return False
        print("Please enter 'yes' or 'no'.")


# GAME INITIALIZATION:
def initialize_game():
    while True:
        n_players = int(input("How many players are playing?: "))
        if n_players >= 2:
            break
        print("Need at least 2 players.")
    while True:
        target = int(
            input("What would you like the target score to be?: "))
        if target > 5:
            break
        print("Target score must be 5 or greater")
    scoreboard = {f'Player {i+1}': 0 for i in range(n_players)}

    return n_players, target, scoreboard


# TAKE TURN:
def take_turn(player, scoreboard):
    roll_count = 0
    turn_score = 0
    while True:
        # Print scoreboard and roll count:
        print("-" * 40)
        print(f"{player}'s turn. See current scoreboard below:\n")
        for player_index, score in scoreboard.items():
            print(f"{player_index}: {score}")
        if roll_count > 0:
            if roll_count == 1:
                print(
                    f"\nYou have rolled {roll_count} time this turn. Your current score for this turn is {turn_score}.")
            else:
                print(
                    f"\nYou have rolled {roll_count} times this turn. Your current score for this turn is {turn_score}.")
        # Roll prompt
        if yes_or_no(f"{player}, want to roll? "):
            roll = dice_roll()
            roll_count += 1
            if roll[0] == 1 and roll[1] == 1:
                print(
                    f"\nYou rolled snake eyes and got super skunked! Your total score is reset to 0.")
                scoreboard[player] = 0
                turn_score = 0
                break
            elif roll[0] == 1 or roll[1] == 1:
                print(
                    f"\nYou rolled a {roll[0]} and a {roll[1]} and got skunked! You lose all points for this turn.")
                scoreboard[player] -= turn_score
                turn_score = 0
                break
            else:
                print(
                    f"\nYou rolled a {roll[0]} and a {roll[1]} for a total of {sum(roll)} points.")
                turn_score += sum(roll)
                scoreboard[player] += sum(roll)
        else:
            break
    print(
        f"You scored {turn_score} points this turn and now have {scoreboard[player]} points.\n")


# MAIN GAME LOOP:
def play_game():
    n_players, target, scoreboard = initialize_game()
    while True:
        for player in scoreboard.keys():
            take_turn(player, scoreboard)
            if max(scoreboard.values()) >= target:
                # Give remaining players their last chance
                players = list(scoreboard.keys())
                remaining = players[players.index(player) + 1:]
                if remaining:
                    print("-" * 40)
                    print(
                        f"{max(scoreboard, key=scoreboard.get)} has reached the target! Remaining players get one last chance!")
                for last_player in remaining:
                    take_turn(last_player, scoreboard)
                # Announce winner
                winner = max(scoreboard, key=scoreboard.get)
                print(f"\n{winner} wins with {scoreboard[winner]} points!")
                return


play_game()
