#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'


class EmptyModel:
    @staticmethod
    def score(*args, **kwargs):
        if args or kwargs:
            return 0

    @staticmethod
    def predict(*args, **kwargs):
        if args or kwargs:
            return 0


def normalize(text):
    letters = []
    for letter in text.lower():
        if letter in ALPHABET:
            letters.append(letter)
        elif letter in ".?!":
            letters.append(' ')
            letters.append('.')
            letters.append(' ')
        else:
            letters.append(' ')
    text = ''.join(letters)
    text = ' '.join(text.split())
    return text


assert normalize('AsD?! d!@$%^^ ee   ') == 'asd . . d . ee'


def load_text(file_name):
    with codecs.open(file_name, 'r', 'utf-8') as f:
        data = f.read()
        return normalize(data).split()


def load_alphabet(file_name):
    global ALPHABET
    with codecs.open(file_name, 'r', 'utf-8') as f:
        data = f.read()
        data = data.strip().lower()
        ALPHABET = data


def generate_sentences(words):
    sentences = []
    current_sentence = []
    for w in words:
        if w == '.':
            if current_sentence:
                sentences.append(current_sentence)
            current_sentence = []
        else:
            current_sentence.append(w)
    if current_sentence:
        sentences.append(current_sentence)
    return sentences
