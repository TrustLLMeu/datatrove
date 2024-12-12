from .base import Record, Bound, TrustLLMFilter
from functools import cache
from collections import Counter
from itertools import tee, islice

import regex as re
import nltk
import math

re.DEFAULT_VERSION = re.V1

PARA_SPLITTER = re.compile(r'\n{2,}')
LINE_SPLITTER = re.compile(r'\n+')
PUNCT_SPAN = re.compile(r'\p{P}+')

def ratio(a, b):
    if b > 0:
        return a / b
    else:
        return None

def mean(xs):
    w = 0
    v = 0
    for x in xs:
        w += 1
        v += (x - v) / w
    return v

def find_duplicates(xs):
    counts = Counter(xs)
    
    tot_elems = 0
    dup_elems = 0
    tot_chars = 0
    dup_chars = 0

    for x, c in counts.items():
        dup_elems += c - 1
        tot_elems += c
        dup_chars += len(x) * (c-1)
        tot_chars += len(x) * c


    return ratio(dup_elems, tot_elems), ratio(dup_chars, tot_chars)

def ngrams(xs, n):
    iterables = tee(xs, n)
    for i, sub in enumerate(iterables):
        list(islice(sub, i)) # drop the first i values from the ith iterable (list forces the slice)
    return zip(*iterables)

def top_duplicate_chars(xss):
    match Counter(xss).most_common(1):
        case [(val, count)]:
            return sum(map(len, val)) * count
        case []:
            return 0

def ngram_duplicate_chars(xss):
    seen = set()
    lb = 0 # left bound of duplicates already accounted for (in the ngram)
    dup_chars = 0
    for xs in xss:
        # we observe one more word, so decrement the left bound.
        lb = max(0, lb - 1)
        if xs in seen:
             # add word lens for words not already accounted for.
             # and set the left bound to the rightmost position
            dup_chars += sum(len(x) for x in xs[lb:])
            lb = len(xs)
        else:
            seen.add(xs)
    return dup_chars

def entropy(counts):
    z = counts.total()
    if z == 0:
        return 0
    else:
        zl = math.log(z)

        ret = 0

        for x, c in counts.items():
            ret -= c/z * (math.log(c) - zl)

        return ret

def efficiency(xs):
    counts = Counter(xs)
    if len(counts) <= 1:
        return 1
    else:
        z = counts.total()
        hmax = math.log(len(counts))
        ret = 0
        for x, c in counts.items():
            p = c / z
            ret -= p * math.log(p) / hmax
        return ret

class RepetitionRecord(Record):
    def __init__(self, doc):
        self.doc = doc
        self.text = doc.text.lower().strip()

    def paras(self):
        return [stripped for para in PARA_SPLITTER.split(self.text) if len(stripped := para.strip()) > 0]

    def lines(self):
        return [stripped for line in LINE_SPLITTER.split(self.text) if len(stripped := line.strip()) > 0]

    @cache
    def _dup_paras(self):
        return find_duplicates(self.paras())

    @cache
    def _dup_lines(self):
        return find_duplicates(self.lines())

    def dup_para_ratio(self):
        return self._dup_paras()[0]

    def dup_para_char_ratio(self):
        return self._dup_paras()[1]

    def dup_line_ratio(self):
        return self._dup_lines()[0]

    def dup_line_char_ratio(self):
        return self._dup_lines()[1]

    @cache
    def words(self):
        return nltk.tokenize.word_tokenize(self.text)

    @cache
    def word_charlen(self):
        return sum(len(w) for w in self.words())

    def dup_ngram_char_ratio(self, n):
        # gopher repetition
        return ratio(ngram_duplicate_chars(ngrams(self.words(), n)), self.word_charlen())

    def top_ngram_char_ratio(self, n):
        # gopher repetition
        return ratio(top_duplicate_chars(ngrams(self.words(), n)), self.word_charlen())

    def top_1gram_char_ratio(self):
        # gopher repetition
        return self.top_ngram_char_ratio(1)

    def top_2gram_char_ratio(self):
        # gopher repetition
        return self.top_ngram_char_ratio(2)

    def top_3gram_char_ratio(self):
        # gopher repetition
        return self.top_ngram_char_ratio(3)

    def top_4gram_char_ratio(self):
        # gopher repetition
        return self.top_ngram_char_ratio(4)

    def dup_5gram_char_ratio(self):
        # gopher repetition
        return self.dup_ngram_char_ratio(5)

    def dup_6gram_char_ratio(self):
        # gopher repetition
        return self.dup_ngram_char_ratio(6)

    def dup_7gram_char_ratio(self):
        # gopher repetition
        return self.dup_ngram_char_ratio(7)

    def dup_8gram_char_ratio(self):
        # gopher repetition
        return self.dup_ngram_char_ratio(8)

    def dup_9gram_char_ratio(self):
        # gopher repetition
        return self.dup_ngram_char_ratio(9)

    def dup_10gram_char_ratio(self):
        # gopher repetition
        return self.dup_ngram_char_ratio(10)

    def efficiency(self):
        # modified SWEb
        return efficiency(self.words())


REPETITION_BOUNDS = {
        'dup_line_ratio': Bound(high=.3),
        'dup_line_char_ratio': Bound(high=.3),
        'dup_para_ratio': Bound(high=.3),
        'dup_para_char_ratio': Bound(high=.3),
        'top_2gram_char_ratio': Bound(high=.2),
        'top_3gram_char_ratio': Bound(high=.18),
        'top_4gram_char_ratio': Bound(high=.16),
        'dup_5gram_char_ratio': Bound(high=.15),
        'dup_6gram_char_ratio': Bound(high=.14),
        'dup_7gram_char_ratio': Bound(high=.13),
        'dup_8gram_char_ratio': Bound(high=.12),
        'dup_9gram_char_ratio': Bound(high=.11),
        'dup_10gram_char_ratio': Bound(high=.10),
        'efficiency': Bound(low=0.5, high=0.99)
        }

class RepetitionFilter(TrustLLMFilter):
    name = 'TrustLLM Repetition'

    def __init__(self, exclusion_writer=None, bounds=REPETITION_BOUNDS):
        super().__init__(exclusion_writer, RepetitionRecord, bounds)
