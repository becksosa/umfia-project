# Fair or Unfair Coin:
You flip a coin 3 times and it comes up heads 3 times in a row. What is the probability the coin is an unfair coin? There are multiple ways to solve this problem. Provide as many solutions as you can.
----------------------------------
----------------------------------
Realistically, the problem says I am the one flipping the coin so I would simply look at the coin and if both sides are heads the probability it’s unfair is 1. If one side is heads and one side is tails then the probability the coin is unfair is 0.

For the sake of argument let’s say I don’t look at the coin. Where did the coin come from? If I got it from a magician this would significantly increase the odds it’s unfair, if I picked it up off the street it’s probably unlikely to be a fake coin. There's not really enough information here to solve the problem confidently. However, I would assume this question isn’t being asked with a magician in mind so I made a few assumptions below and attempted to solve it:

------------------
## Solution One: Bayes Theorem
I started by creating a function in python so I could easily call Bayes Theorem as needed:

```python
def bayes_theorem(p_B_given_A, p_A, p_B):
    # P(A|B) = (P(B|A) * P(A)) / P(B)
    return (p_B_given_A * p_A) / p_B
```

Then I defined the relevant events:
 - H3 = the event of getting three heads in a row
 - U = the event of picking the unfair coin
 - F = the event of picking the fair coin

The problem did not specify the odds of selecting an unfair coin. I have chosen to assume that the probability of picking either coin is .5, selected once and flipped three times consecutively without switching coins. My next step was to define the variables with this assumption in mind:

```python
# The probability of selecting either coin:
p_U = 0.5 # unfair
p_F = 0.5 # fair

# P(H3|U) = the probability of getting three heads in a row given that the coin is unfair
p_H3_given_U = 1 ** 3 # 100% chance, 3 times in a row

# P(H3) = the total probability of getting three heads in a row
p_H3_given_F = 0.5 ** 3 # 50% chance, 3 times in a row
p_H3 = p_H3_given_U * p_U + p_H3_given_F * p_F

print(f'P(H3|U) = {p_H3_given_U}')
print(f'P(U) = {p_U}')
print(f'P(H3) = {p_H3}')
```
```
P(H3|U) = 1
P(U) = 0.5
P(H3) = 0.5625
```


Then I applied Bayes Theorem: Solving for the probability a coin is unfair, given that I selected it and flipped it for 3 heads in a row:
```
P(U|H3) = (P(H3|U) * P(U)) / P(H3)
```
In Python:
```python
answer = bayes_theorem(p_H3_given_U,p_U,p_H3)
print(f'P(U|H3) = {round((answer),2)}')
```
```
P(U|H3) = 0.889
```
Based on this analysis, if you select a coin with a 50/50 chance of it being unfair, and flip heads 3 times in a row, the probability that the coin you selected was an unfair coin is .889.

-------------------------------------

## Solution Two: Tree Diagram
I created a tree diagram with this [Tree Diagram Generator](https://kera.name/treediag/) to map the outcomes and probabilities of each event, given the assumption of a 50% chance to choose an unfair coin:

![tree diag](/assets/unfair_coin_tree_diag.jpg)

Based on the diagram, there are two possible paths to 3 heads in a row:
 - Unfair coin probability = .5
 - Fair coin probablity = .0625

I found the probability the coin was unfair given flipping 3 heads in a row by calculating the probability between these two paths of the coin being unfair:


 ```python
 # Path probabilities:
p_U = .5
p_F = .0625
# H3 = the event of flipping 3 heads in a row

# Calculate the probability the coin was unfair given H3 
p_U_given_H3 = p_U / (p_U + p_F)
print(f'''P(U | H3 = {round((p_U_given_H3),3)}%''')
```
Given this analysis, the conclusion is the same.  If you select a coin with a 50/50 chance of it being unfair, and flip heads 3 times in a row, the probability that the coin you selected was an unfair coin is 88.89%
