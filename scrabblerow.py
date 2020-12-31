import datetime
from functools import lru_cache
import copy

# total time to run in milliseconds, set to None for it to never timeout - this
# will find high scores but can take a very long time
RUNTIME = 298000  # 2 seconds short of 5 minutes to be safe
#RUNTIME = None


def author():
    return 'Khatter, Joy'


def student_id():
    return '500866988'


@lru_cache
def get_score(scoring_f, word):
    return scoring_f(word)


class WordOption(object):

    #    represents a valid option to place a given word at a given place in the
    #    pattern

    _score = None

    def __init__(self, word, scoring_f, start_index):
        self._word = word
        self._scoring_f = scoring_f
        self._start_index = start_index

    def __str__(self):
        return self._word

    def __len__(self):
        return len(str(self))

    def items(self):
        for i, c in enumerate(str(self)):
            yield i+self._start_index, str(self)[i]

    @property
    def start_index(self):
    #     index of the start of this word
        return self._start_index

    @property
    def end_index(self):
    #     index of the end of this word
        return self._start_index+len(self)-1

    @property
    def next_index(self):
    #    the start index of the next word after this one
        return self._start_index+len(self)+1

    @property
    def score(self):
     #   cached property of the score, will not change
        if self._score is None:
            self._score = get_score(self._scoring_f, str(self))
        return self._score


class ScrabbleTile(object):

    #    represents a cell on the scrabble row where a letter can be placed.
    #   Container for words that can be placed on it

    _word_options = None
    _word_options_lst = None

    def add_word(self, word_option):

        #    add a word to this tile, it is a word that can validly be placed
        #    starting from this tile

        if self._word_options is None:
            self._word_options = dict()
        try:
            current_option = self._word_options[len(word_option)]
        except KeyError:
            self._word_options[len(word_option)] = word_option
        else:
            if current_option.score < word_option.score:
                self._word_options[len(word_option)] = word_option
                self._word_options_lst = None

    @property
    def word_options(self):

        #   sorted list of words that can be placed here with highest score first

        if self._word_options is None:
            return list()
        elif self._word_options_lst is None:
            self._word_options_lst = sorted(
                list(self._word_options.values()),
                key=lambda w: w.score,
                reverse=True
            )
        return self._word_options_lst

    def __str__(self):
        return self.letter


class WildcardTile(ScrabbleTile):
    # a tile that can take any letter, represetned by '-'

    @property
    def letter(self):
        return '-'


class FixedTile(ScrabbleTile):
    # a tile that is a fixed part of the pattern given

    _letter = ''

    def __init__(self, letter):
        self._letter = letter

    @property
    def letter(self):
        return self._letter


def get_scrabble_tile(letter):

    #   given a letter from the pattern input, return a ScrabbleTile

    if letter == '-':
        return WildcardTile()
    else:
        return FixedTile(letter)


class ScrabbleRow(object):
    # represents the pattern input, container for ScrabbleTiles

    def __init__(self, pattern, scoring_f):
        self._pattern = pattern
        self._tiles = [get_scrabble_tile(c) for c in pattern]
        self._scoring_f = scoring_f

    @property
    def pattern(self):
        return self._pattern

    @property
    def scoring_f(self):
        return self._scoring_f

    def __iter__(self):
        return iter(self._tiles)

    def __getitem__(self, index):
        return self._tiles[index]

    def __len__(self):
        return len(self.pattern)

    def add_scrabble_trees(self):

        #    given a dict of trees of our allowed words, populate this row with
        #   all the words in the trees that can be validly placed on this row
        #   according to the pattern


        global scrabble_trees_by_length

        for length, root in scrabble_trees_by_length.items():
            self._add_scrabble_tree1(root, length)

    def _add_scrabble_tree1(self, root, length):

        #    given a tree and the length of the words it contains, populate this
        #   row with all the words in that tree that can be validly placed on
        #   this row according to the pattern

        for i in range(len(self)-length+1):
            next_index = i+length
            # check next tile to see it's a wildcard (or end of pattern)
            if len(self) > next_index and not isinstance(self[next_index], WildcardTile):
                    continue
            subpattern = self.pattern[i:next_index]
            for word in root.get_matches(subpattern):
                wo = WordOption(word, self.scoring_f, i)
                self[i].add_word(wo)


class ResultRow(object):

    words = None
    timeout = None

    # this is used to track where to start the algorithm when forking
    left_index = 0

    def __init__(self, row, timeout=None):
        self._row = row
        self.words = list()
        self.timeout = timeout

    def __len__(self):
        return len(self._row)

    def add_word(self, word : WordOption):
        # add a word to this solution
        self.words.append(word)

    def __str__(self):
        result = list(self._row.pattern)
        for word in self.words:
            for key, val in word.items():
                result[key] = val
        return ''.join(result)

    @property
    def score(self):
        # not cached on a Row level because rows can change
        return sum(get_score(self._row.scoring_f,str(word)) for word in self.words)

    def has_timedout(self):
        # check to see if time has runout while doing our algorithms
        if self.timeout is None:
            return False
        return datetime.datetime.now() >= self.timeout

    def populate_forking_algorithm(self):

        #    populate with words from left to right, whenever there is more than
        #   one option of a word to place, it recurses on all the options and
        #   returns the one with the highest score

        results = [self]

        while not self.has_timedout() and self.left_index < len(self._row):
            words = self._row[self.left_index].word_options
            if words:
                # there are some words that can be placed here, recurse on
                # copies of this object to see what scores can be achieved
                # using different options
                children = [copy.deepcopy(self) for _ in words]
                words_children = zip(words, children)
                while not self.has_timedout():
                    try:
                        word, child = next(words_children)
                    except StopIteration:
                        break
                    child.add_word(word)
                    child.left_index = word.next_index
                while children and not self.has_timedout():
                    results.append(children.pop(0).populate_forking_algorithm())
                break
            else:
                # no words can be placed here so skip ahead some spaces
                #TODO refactor with isinstance
                prev_char = ''
                while not self.has_timedout() and prev_char != '-' and self.left_index < len(self._row):
                    self.left_index += 1
                    prev_char = str(self._row[self.left_index-1])

        # find the best score in all the forks
        max_score = max(results, key=lambda c: c.score)
        return max_score

    def populate_forking_algorithm2(self):

        #    populate with words from left to right, whenever there is more than
        #   one option of a word to place, it recurses on all the options and
        #   returns the one with the highest score

        results = [self]
        while not self.has_timedout() and self.left_index < len(self._row):
            words = self._row[self.left_index].word_options
            if words:
                children = [copy.deepcopy(self) for _ in words]
                words_children = zip(words, children)
                while not self.has_timedout():
                    try:
                        word, child = next(words_children)
                    except StopIteration:
                        break
                    child.add_word(word)
                    child.left_index = word.next_index
                while children and not self.has_timedout():
                    results.append(children.pop(0).populate_forking_algorithm2())
            #TODO refactor with isinstance
            prev_char = ''
            while not self.has_timedout() and prev_char != '-' and self.left_index < len(self._row):
                self.left_index += 1
                prev_char = str(self._row[self.left_index-1])
        max_score = max(results, key=lambda c: c.score)
        return max_score


# dict of trees to store the words input with keys being the word length
scrabble_trees_by_length = None


def _split_string_at_index(string, index):
    # given a string, split before the index given and return 2 strings
    _, head, tail = string.partition(string[:index])
    return head, tail


class ScrabbleTree(object):
    # tree for all words of one length

    def __init__(self):
        self.children = {}

    def insert_word(self, word_iter):

        #    put a word into the tree, creates new children if they don't exist
        #   and recurses

        try:
            letter = next(word_iter)
        except StopIteration:
            return
        child = self.children.get(letter, ScrabbleTree())
        child.insert_word(word_iter)
        self.children[letter] = child

    def get_matches(self, pattern, word_so_far=''):

        #    given a pattern, yield words from the tree that match the pattern

        if not pattern:
            yield word_so_far + ''
        elif pattern[0] == '-':
            for letter, child in self.children.items():
                for word in child.get_matches(pattern[1:], word_so_far+letter):
                    yield word
        elif pattern[0] in self.children:
            letter = pattern[0]
            child = self.children[letter]
            for word in child.get_matches(pattern[1:], word_so_far+letter):
                yield word


def init_scrabble_tree(words, scoring_f):

    #    create the tree of the words, do this globally once because it is slow


    global scrabble_trees_by_length
    global setup_ended_time

    if scrabble_trees_by_length is None:
        scrabble_trees_by_length = {}
        for word in words:
            root = scrabble_trees_by_length.get(len(word), ScrabbleTree())
            root.insert_word(iter(word))
            scrabble_trees_by_length[len(word)] = root

    # this will be used to decide a fair share of time given to each round
    setup_ended_time = datetime.datetime.now()


def get_timeout():

    global end_time
    global setup_ended_time

    if end_time is not None:
        try:
            from scrabblerun import rounds
        except (ImportError, ModuleNotFoundError):
            rounds = 50
        return datetime.datetime.now() + datetime.timedelta(seconds=(end_time-setup_ended_time).total_seconds()/rounds)
    else:
        return None


def fill_words(pattern, words, scoring_f, minlen, maxlen):

    init_scrabble_tree(words, scoring_f)

    timeout = get_timeout()

    # put all the words from our tree into the row
    row = ScrabbleRow(pattern, scoring_f)
    row.add_scrabble_trees()

    # of the words in the row, find the one that gives the best score
    result = ResultRow(row, timeout=timeout)
    result = result.populate_forking_algorithm()

    # if we have some time left, try the other algorithm because there is a
    # small chance we can find a better result
    if timeout is None or datetime.datetime.now() < timeout:
        result2 = ResultRow(row, timeout=timeout)
        result2 = result2.populate_forking_algorithm2()
        if result2.score > result.score:
            return str(result2)

    return str(result)


# keep track of the time this was imported so that it can end in time
if RUNTIME is not None:
    end_time = datetime.datetime.now() + datetime.timedelta(milliseconds=RUNTIME)
else:
    end_time = None
