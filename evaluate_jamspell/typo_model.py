#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import bisect

from scipy.stats import binom

from evaluate_jamspell.utils import ALPHABET

# todo: calculate correct typo probabilities

TYPO_PROB = 0.03  # chance of making typo for a single letter
SECOND_TYPO_CF = 0.2  # chance of making two typos, relative to TYPO_PROB
REPLACE_PROB = 0.7
INSERT_PROB = 0.1
REMOVE_PROB = 0.1
TRANSPOSE_PROB = 0.1
TRANSPOSE_DISTANCE_PROB = [0.8, 0.15, 0.04, 0.01]
EPSILON = 0.001

assert 1.0 >= TYPO_PROB > 0
assert abs(REPLACE_PROB + INSERT_PROB + REMOVE_PROB + TRANSPOSE_PROB - 1.0) < EPSILON


# Randomly selects a value from list [(value, weight), ... ]
def weighted_choice(values):
    values, weights = zip(*values)
    total_weight = sum(weights)
    sum_weight = 0.
    distribution = []
    for w in weights:
        sum_weight += w
        distribution.append(sum_weight / total_weight)
    return values[bisect.bisect(distribution, random.random())]


def typo_replace(word):
    if not word:
        return word
    fragment_length = random.randint(0, len(word) - 1)
    return word[:fragment_length] + random.choice(ALPHABET) + word[fragment_length + 1:]


def typo_insert(word):
    fragment_length = random.randint(0, len(word))
    return word[:fragment_length] + random.choice(ALPHABET) + word[fragment_length:]


def typo_remove(word):
    if not word:
        return word
    fragment_length = random.randint(0, len(word) - 1)
    return word[:fragment_length] + word[fragment_length + 1:]


def swap_letter(s, i, j):
    lst = list(s)
    lst[i], lst[j] = lst[j], lst[i]
    return ''.join(lst)


def typo_transpose(word):
    if not word:
        return word
    fragment_length = random.randint(0, len(word) - 1)
    d = weighted_choice(enumerate(TRANSPOSE_DISTANCE_PROB)) + 1
    l1 = max(0, fragment_length - d // 2)
    l2 = min(len(word) - 1, l1 + d)
    return swap_letter(word, l1, l2)


TYPO_TYPES = [REPLACE_PROB, INSERT_PROB, REMOVE_PROB, TRANSPOSE_PROB]
TYPO_GENERATORS = [typo_replace, typo_insert, typo_remove, typo_transpose]

LEN_TO_PROB = {}


def get_word_typo_chance(word):
    word_length = len(word)
    prob = LEN_TO_PROB.get(word_length)
    if prob is None:
        no_typo_chance = 1.0 - TYPO_PROB
        prob = 1.0 - binom.pmf(word_length, word_length, no_typo_chance)
    LEN_TO_PROB[word_length] = prob
    return prob


def generate_typo(word):
    if word == '.':
        return word

    chance = random.random()
    required = get_word_typo_chance(word)
    num_typo = 0

    if chance < required:
        num_typo = 1
    if chance < required * SECOND_TYPO_CF:
        num_typo = 2

    for _ in range(num_typo):
        typo_type = weighted_choice(enumerate(TYPO_TYPES))
        word = TYPO_GENERATORS[typo_type](word)
    return word
