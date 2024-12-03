from .base import Record, Bound, TrustLLMFilter
from functools import cache
import regex as re

re.DEFAULT_VERSION = re.V1

LETTER = re.compile(r'\p{L}')
LATIN = re.compile(r'\p{latin}')
LATIN_SPAN = re.compile(r'\p{latin}+')
START_OF_WORD = re.compile(r'\m')
SPACE_SPAN = re.compile(r'\s+')

LINE_SPLITTER = re.compile(r'\n+')

INIT_BULLET = re.compile(r'^(?:•|-)')
INIT_PUNCT = re.compile(r'^\p{P}')
END_PUNCT = re.compile(r'\p{P}$')
ELLIPSIS = re.compile(r'\u2026|\.(\s?\.)\1{1,}')
END_ELLIPSIS = re.compile(r'(?:\u2026|\.(\s?\.)\1{1,})$')

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


class PrefilterRecord(Record):
    def __init__(self, doc):
        self.doc = doc
        self.text = doc.text.lower().strip()

    @cache
    def words(self):
        return SPACE_SPAN.split(self.text)

    @cache
    def num_latin_chars(self):
        return sum(1 for _ in LATIN.finditer(self.text))

    @cache
    def num_script_chars(self):
        return sum(1 for _ in LETTER.finditer(self.text))
    
    @cache
    def num_words(self):
        return len(self.words())

    @cache
    def num_latin_words(self):
        return sum(1 for w in self.words() if LATIN.search(w))

    def latin_word_ratio(self):
        return ratio(
                self.num_latin_words(),
                self.num_words()
            )

    def latin_script_ratio(self):
        return ratio(
                self.num_latin_chars(),
                self.num_script_chars(),
                )

    def average_word_len(self):
        return ratio(
                len(self.text),
                self.num_words()
                )

    def ellipsis_ratio(self):
        # gopher quality
        return ratio(sum(1 for _ in ELLIPSIS.finditer(self.text)), self.num_words())

    def hashbang_ratio(self):
        # gopher quality
        return ratio(self.text.count('#'), self.num_words())
    
    @cache
    def _line_stats(self):
        num_lines = 0
        init_bullet = 0
        end_punct = 0
        end_ellipsis = 0
        short_lines = 0
        for line in LINE_SPLITTER.splititer(self.text):
            line = line.strip()
            if line:
                num_lines += 1
                init_bullet += 1 if INIT_BULLET.match(line) else 0
                end_punct += 1 if END_PUNCT.match(line) else 0
                end_ellipsis += 1 if END_ELLIPSIS.match(line) else 0
                short_lines += 1 if len(line) < 30 else 0

        return {
                'num_lines': num_lines, 
                'init_bullets': init_bullet, 
                'end_punct': end_punct, 
                'end_ellipsis': end_ellipsis,
                'short_lines': short_lines
                }

    def num_lines(self):
        return self._line_stats()['num_lines']

    def init_bullets(self):
        return self._line_stats()['init_bullets']

    def end_punct(self):
        return self._line_stats()['end_punct']

    def end_ellipsis(self):
        return self._line_stats()['end_ellipsis']

    def short_lines(self):
        return self._line_stats()['short_lines']

    def words_per_line(self):
        return ratio(self.num_words(), self.num_lines())

    def short_line_ratio(self):
        return ratio(self.short_lines(), self.num_lines())

    def init_bullet_ratio(self):
        return ratio(self.init_bullets(), self.num_lines())

    def end_punct_ratio(self):
        return ratio(self.end_punct(), self.num_lines())

    def end_ellipsis_ratio(self):
        return ratio(self.end_ellipsis(), self.num_lines())


PREFILTER_BOUNDS = {
        'latin_word_ratio': Bound(low=.8),
        'latin_script_ratio': Bound(low=.5),
        'num_words': Bound(low=50, high=100000),
        'average_word_len': Bound(low=3, high=15),
        'hashbang_ratio': Bound(high=0.1),
        'ellipsis_ratio': Bound(high=0.1),
        'init_bullet_ratio': Bound(high=0.9),
        'end_ellipsis_ratio': Bound(high=0.3),
        'short_line_ratio': Bound(high=0.67),
        'words_per_line':  Bound(low=10/3),
        }

class PreFilter(TrustLLMFilter):
    name = 'TrustLLM PreFilter'

    def __init__(self, exclusion_writer=None, bounds=PREFILTER_BOUNDS):
        super().__init__(exclusion_writer, PrefilterRecord, bounds)
