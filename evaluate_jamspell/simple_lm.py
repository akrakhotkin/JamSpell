#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import zlib
import math
import sys
import time

from collections import defaultdict

from evaluate_jamspell.utils import load_text, normalize, generate_sentences


class SimpleLangModel(object):
    K = 0.05

    def __init__(self):
        self.wordToId = {}  # word => int id
        self.idToWord = {}  # int id => word
        self.lastID = 0
        self.totalWords = 0
        self.gram1 = defaultdict(int)  # word => count
        self.gram2 = defaultdict(int)  # (word1, word2) => count
        self.gram3 = defaultdict(int)  # (word1, word2, word3) => count

    def train(self, train_file):
        print('[info] loading text')
        text = load_text(train_file)
        sentences = generate_sentences(text)
        sentences = self.convert_to_ids(sentences)

        print('[info] generating N-grams', len(sentences))
        total = len(sentences)
        last_time = time.time()
        for i in range(0, total):
            sentence = sentences[i]
            for w in sentence:
                self.gram1[w] += 1
                self.totalWords += 1
            for j in range(len(sentence) - 1):
                self.gram2[(sentence[j], sentence[j + 1])] += 1
            for j in range(len(sentence) - 2):
                self.gram3[(sentence[j], sentence[j + 1], sentence[j + 2])] += 1
            if time.time() - last_time >= 4.0:
                last_time = time.time()
                print('[info] processed %.2f%%' % (100.0 * i / total))

        print('[info] finished training')

    def convert_to_ids(self, sentences):
        new_sentences = []
        for s in sentences:
            new_sentence = []
            for w in s:
                new_sentence.append(self.get_word_id(w))
            new_sentences.append(new_sentence)
        return new_sentences

    def get_word_id(self, word, add=True):
        wid = self.wordToId.get(word)
        if wid is None:
            if add:
                self.lastID += 1
                wid = self.lastID
                self.wordToId[word] = wid
                self.idToWord[wid] = word
            else:
                return -1
        return wid

    def save(self, model_file):
        with open(model_file, 'wb') as f:
            data = zlib.compress(pickle.dumps(self.__dict__, -1))
            f.write(data)

    def load(self, model_file):
        with open(model_file, 'rb') as f:
            data = pickle.loads(zlib.decompress(f.read()))
            self.__dict__.clear()
            self.__dict__.update(data)
            assert self.gram1 and self.gram2 and self.gram3

    def get_gram_1_prob(self, word_id):
        word_counts = self.gram1.get(word_id, 0) + SimpleLangModel.K
        vocab_size = len(self.gram1)
        return float(word_counts) / (self.totalWords + vocab_size)

    def get_gram_2_prob(self, word_id_1, word_id_2):
        counts_word_1 = self.gram1.get(word_id_1, 0) + self.totalWords
        counts_bigram = self.gram2.get((word_id_1, word_id_2), 0) + SimpleLangModel.K
        return float(counts_bigram) / counts_word_1

    def get_gram_3_prob(self, word_id_1, word_id_2, word_id_3):
        counts_gram_2 = self.gram2.get((word_id_1, word_id_2), 0) + self.totalWords
        counts_gram_3 = self.gram3.get((word_id_1, word_id_2, word_id_3), 0) + SimpleLangModel.K
        return float(counts_gram_3) / counts_gram_2

    def predict(self, sentence):
        sentence = [self.get_word_id(w, False) for w in normalize(sentence).split()] + [None] * 2
        result = 0
        for i in range(0, len(sentence) - 2):
            p2 = self.get_gram_3_prob(sentence[i], sentence[i + 1], sentence[i + 2])
            p3 = self.get_gram_2_prob(sentence[i], sentence[i + 1])
            p4 = self.get_gram_1_prob(sentence[i])
            result += math.log(p2 * p3 * p4)
        return result


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: %s trainFile model.bin' % sys.argv[0])
        sys.exit(42)

    trainFile = sys.argv[1]
    modelFile = sys.argv[2]

    model = SimpleLangModel()
    model.train(trainFile)
    model.save(modelFile)
