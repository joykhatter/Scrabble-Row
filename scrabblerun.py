import scrabblerow as sr
from random import Random

version = 'August 22, 2020'

# Separator character denoting a blank space.

sep = '-'

# Seed for the random number generator that produces the patterns.
seed = 4444

# Length of the random patterns.

patlen = 40

# Minimum and maximum length of words accepted in solutions.

minlen, maxlen = 4, 30

# How many rounds to play this game.

rounds = 10

# Maximum possible consecutive run of blanks in the pattern.

mb = 5

# Percentage probability of the current run of blanks to continue.

bp = 30

# Scrabble letter values in the standard American English version.

letter_values = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2,
    'h': 4, 'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1,
    'o': 1, 'p': 3, 'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1,
    'v': 4, 'w': 4, 'x': 8, 'y': 4, 'z': 10
    }

# Dictionary used to count the frequency of each letter.

letter_counts = {c: 0 for c in letter_values}


# Word scoring function for scrabble.

def scrabble_value(word):
    if minlen <= len(word) <= maxlen:
        return sum(letter_values.get(c, 0) for c in word)
    else:

        return 0


def length_squared(word):
    if minlen <= len(word) <= maxlen:
        return len(word) ** 2
    else:
        return 0


# Create a random pattern of the given length.

def create_pattern(n, rng):
    prev, result, blanks = '', '', 0
    letters = "".join(sorted([c for c in letter_counts]))
    letter_freqs = [letter_counts[c] for c in letters]
    for i in range(n):
        if blanks < mb and (prev != sep or rng.randint(0, 99) < bp):
            prev = sep
            blanks += 1
        else:
            prev = rng.choices(letters, letter_freqs, k=1)[0]
            blanks = 0
        result += prev
    return result


def score_answer(result, pattern, scoring_f):
    curr, score = '', 0
    for (pos, (c1, c2)) in enumerate(zip(result + sep, pattern + sep)):
        if c2 != sep and c1 != c2:
            print(f"\nPATTERN MISMATCH AT POSITION {pos}!!!")
            return 0
        if c1 == sep:
            if curr in wordset:
                score += scoring_f(curr)
            elif len(curr) > 1:
                print(f"\nUNKNOWN WORD {curr} AT POSITION {pos}!!!")
                return 0
            curr = ''
        else:
            curr += c1
    return score


def play_one_round(pattern, scoring_f):
    score = 0
    print(f"\nPattern: {pattern}")
    try:
        result = sr.fill_words(pattern, words, scoring_f, minlen, maxlen)
    except Exception as e:
        print(f"CRASH!!! {e}")
        return 0
    print(f"Result : {result} ", end='')
    if len(result) == len(pattern):
        score += score_answer(result, pattern, scoring_f)
    else:
        print(f"\nRESULT AND PATTERN LENGTHS DIFFERENT!!!")
    print(f"({score})")
    return score


def play():
    print(f"Scrabblerun tester by Ilkka Kokkarinen, {version}.")
    print(f"Settings seed={seed}, patlen={patlen}, rounds={rounds}.")

    def scoring_f(w):
        return length_squared(w) + scrabble_value(w)

    testcases = []  # Fill in your testcase strings inside this list.
    for pattern in testcases:
        play_one_round(pattern, scoring_f)

    total, rng = 0, Random(seed)
    for r in range(rounds):
        pattern = create_pattern(patlen, rng)
        total += play_one_round(pattern, scoring_f)
    print(f"{total} {sr.author()} {sr.student_id()}")


with open('words_sorted.txt', 'r', encoding='utf-8') as f:
    words = [x.strip() for x in f]
    words = [x for x in words if minlen <= len(x) <= maxlen]
    wordset = set(words)
    for word in words:
        for c in word:
            letter_counts[c] += 1

if __name__ == '__main__':
    play()