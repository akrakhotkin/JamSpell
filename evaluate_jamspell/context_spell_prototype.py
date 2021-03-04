import re

from collections import Counter

from evaluate_jamspell.simple_lm import SimpleLangModel
from evaluate_jamspell.utils import EmptyModel

WORDS = Counter()
TOTAL_WORDS = 0
LANG_MODEL = EmptyModel()
WEIGHTS = {
    0: 1.0,
    1: 1.08,
    2: 50.0,
}


def words(text): return re.findall(r'\w+', text.lower())


def init(filename='big.txt', model_name='big.bin'):
    global WORDS
    global TOTAL_WORDS
    global LANG_MODEL
    WORDS = Counter(words(open(filename).read()))
    TOTAL_WORDS = sum(WORDS.values())
    LANG_MODEL = SimpleLangModel()
    LANG_MODEL.load(model_name)


def prob(word, sentence, pos):
    word, level = word
    sub_sentence = sentence[pos-3:pos] + [word] + sentence[pos+1:pos+4]
    sub_sentence = ' '.join(sub_sentence)
    score = LANG_MODEL.predict(sub_sentence)
    return score * WEIGHTS[level]


def correction(sentence, pos):
    """Most probable spelling correction for word."""
    word = sentence[pos]
    variants = candidates(word)
    if not variants:
        variants = candidates(word, False)
    if not variants:
        return word
    variants = sorted(variants, key=lambda w: prob(w, sentence, pos), reverse=True)
    variants = [c[0] for c in variants]
    return variants


def candidates(word, nearest=True):
    res = {}
    variants = ((0, [word]), (1, edits1(word))) if nearest else ((2, edits2(word)),)
    for lvl, w0rds in variants:
        for w in w0rds:
            if w in WORDS:
                res.setdefault(w, lvl)
    return res.items()


def edits1(word):
    """All edits that are one edit away from `word`."""
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    """All edits that are two edits away from `word`."""
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))
