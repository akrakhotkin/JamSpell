#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import argparse
import time
import copy


from evaluate_jamspell.typo_model import generate_typo
from evaluate_jamspell.utils import normalize, load_text, generate_sentences, load_alphabet


class STATE:
    NONE = 0
    LETTER = 1
    DOT = 2
    SPACE = 3


def generate_typos(text):
    return list(map(generate_typo, text))


class Corrector(object):
    def __init__(self):
        pass

    def correct(self, sentence, position):
        pass


class DummyCorrector(Corrector):
    def __init__(self):
        super(DummyCorrector, self).__init__()

    def correct(self, sentence, position):
        return sentence[position]


class HunspellCorrector(Corrector):
    def __init__(self, model_path):
        super(HunspellCorrector, self).__init__()
        import hunspell
        self.__model = hunspell.HunSpell(model_path + '.dic', model_path + '.aff')

    def correct(self, sentence, position):
        word = sentence[position]
        if self.__model.spell(word):
            return word
        return self.__model.suggest(word)


class NorvigCorrector(Corrector):
    def __init__(self, train_file):
        super(NorvigCorrector, self).__init__()
        import norvig_spell
        norvig_spell.init(train_file)

    def correct(self, sentence, position):
        word = sentence[position]
        import norvig_spell
        return norvig_spell.correction(word)


class ContextCorrector(Corrector):
    def __init__(self, model_path):
        super(ContextCorrector, self).__init__()
        import context_spell
        context_spell.init(model_path + '.txt', model_path + '.binary')

    def correct(self, sentence, position):
        import context_spell
        return context_spell.correction(sentence, position)


class ContextPrototypeCorrector(Corrector):
    def __init__(self, model_path):
        super(ContextPrototypeCorrector, self).__init__()
        import context_spell_prototype
        context_spell_prototype.init(model_path + '.txt', model_path + '.bin')

    def correct(self, sentence, position):
        import context_spell_prototype
        return context_spell_prototype.correction(sentence, position)


class JamspellCorrector(Corrector):
    def __init__(self, model_file):
        super(JamspellCorrector, self).__init__()
        import jamspell
        self.model = jamspell.TSpellCorrector()
        # self.model.SetPenalty(16.0, 0.0)
        if not (self.model.LoadLangModel(model_file)):
            raise Exception('wrong model file: %s' % model_file)

    def correct(self, sentence, position):
        candidates = list(self.model.GetCandidates(sentence, position))
        if len(candidates) == 0:
            return sentence[position]
        return candidates


def evaluate_corrector(corrector_name, corrector, original_sentences, errored_sentences, max_words=None):
    total_errors = 0
    orig_errors = 0
    fixed_errors = 0
    broken = 0
    total_not_touched = 0
    top_n_total_errors = 0
    top_n_fixed = 0

    errored_sentences = copy.deepcopy(errored_sentences)

    start_time = last_time = time.time()
    n = 0
    for sentID in range(len(original_sentences)):
        original_text = original_sentences[sentID]
        errored_text = errored_sentences[sentID]
        for pos in range(len(original_text)):
            errored_word = errored_text[pos]
            original_word = original_text[pos]
            fixed_candidates = corrector.correct(errored_text, pos)
            if isinstance(fixed_candidates, list):
                fixed_candidates = fixed_candidates[:7]
                fixed_word = fixed_candidates[0]
                fixed_words = set(fixed_candidates)
            else:
                fixed_word = fixed_candidates
                fixed_words = [fixed_candidates]

            # if original_word != fixed_word:
            #    print('%s (%s=>%s):\n%s\n\n' % (original_word, errored_word, fixed_word, ' '.join(errored_text)))

            errored_text[pos] = fixed_word
            n += 1

            if errored_word != original_word:
                orig_errors += 1
                if fixed_word == original_word:
                    fixed_errors += 1
                if fixed_word != errored_word and original_word in fixed_candidates:
                    top_n_fixed += 1
            else:
                total_not_touched += 1
                if fixed_word != original_word:
                    broken += 1
                    # print(original_word, fixed_word)

            if fixed_word != original_word:
                total_errors += 1

            if original_word not in fixed_words:
                top_n_total_errors += 1

            if sentID % 1 == 0 and pos and time.time() - last_time > 4.0:
                progress = float(sentID) / len(original_sentences)
                err_rate = float(total_errors) / n
                if max_words is not None:
                    progress = float(n) / max_words
                print('[debug] %s: processed %.2f%%, error rate: %.2f%%' % (corrector_name,
                                                                            100.0 * progress,
                                                                            100.0 * err_rate))
                last_time = time.time()

            if max_words is not None and n >= max_words:
                break

        if max_words is not None and n >= max_words:
            break

        # if fixed_word != original_word:
        #    print(original_word, errored_word, fixed_word)

    return (float(total_errors) / n,
            float(fixed_errors) / orig_errors,
            float(broken) / total_not_touched,
            float(top_n_total_errors) / n,
            float(top_n_fixed) / orig_errors,
            time.time() - start_time)


def test_mode(corrector):
    while True:
        sentence = input(">> ").lower().strip()
        sentence = normalize(sentence).split()
        if not sentence:
            continue
        new_sentence = []
        for i in range(len(sentence)):
            fix = corrector.correct(sentence, i)
            if isinstance(fix, list):
                fix = fix[0]
            new_sentence.append(fix)
        print(' '.join(new_sentence))


def evaluate_jamspell(model_file, test_text, alphabet_file, max_words=50000):
    load_alphabet(alphabet_file)
    corrector = JamspellCorrector(model_file)
    random.seed(42)
    original_text = load_text(test_text)
    errored_text = generate_typos(original_text)
    assert len(original_text) == len(errored_text)
    original_sentences = generate_sentences(original_text)
    errored_sentences = generate_sentences(errored_text)
    errors_rate, fix_rate, broken, top_n_err, top_n_fix, exec_time = \
        evaluate_corrector('jamspell', corrector, original_sentences, errored_sentences, max_words)
    return errors_rate, fix_rate, broken, top_n_err, top_n_fix


def main():
    parser = argparse.ArgumentParser(description='spelling correctors evaluation')
    parser.add_argument('file', type=str, help='text file to use for evaluation')
    parser.add_argument('-hs', '--hunspell', type=str, help='path to hunspell model')
    parser.add_argument('-ns', '--norvig', type=str, help='path to train file for Norvig spell corrector')
    parser.add_argument('-cs', '--context', type=str, help='path to context spell model')
    parser.add_argument('-csp', '--context_prototype', type=str, help='path to context spell prototype model')
    parser.add_argument('-jsp', '--jamspell', type=str, help='path to jamspell model file')
    parser.add_argument('-t', '--test', action="store_true")
    parser.add_argument('-mx', '--max_words', type=int, help='max words to evaluate')
    parser.add_argument('-a', '--alphabet', type=str, help='alphabet file')
    args = parser.parse_args()

    if args.alphabet:
        load_alphabet(args.alphabet)

    correctors = {
        'dummy': DummyCorrector(),
    }

    corrector = correctors['dummy']

    max_words = args.max_words

    print('[info] loading models')

    if args.hunspell:
        correctors['hunspell'] = corrector = HunspellCorrector(args.hunspell)

    if args.norvig:
        correctors['norvig'] = corrector = NorvigCorrector(args.norvig)

    if args.context:
        correctors['context'] = corrector = ContextCorrector(args.context)

    if args.context_prototype:
        correctors['prototype'] = corrector = ContextPrototypeCorrector(args.context_prototype)

    if args.jamspell:
        correctors['jamspell'] = corrector = JamspellCorrector(args.jamspell)

    if args.test:
        return test_mode(corrector)

    random.seed(42)
    print('[info] loading text')
    original_text = load_text(args.file)
    original_text_length = len(list(original_text))

    print('[info] generating typos')
    errored_text = generate_typos(original_text)
    errored_text_length = len(list(errored_text))

    assert original_text_length == errored_text_length

    original_sentences = generate_sentences(original_text)
    errored_sentences = generate_sentences(errored_text)

    assert len(original_sentences) == len(errored_sentences)

    # for s in original_sentences[:50]:
    #    print(' '.join(s) + '.')

    print('[info] total words: %d' % len(original_text))
    print('[info] evaluating')

    results = {}

    for correctorName, corrector in correctors.items():
        errors_rate, fix_rate, broken, top_n_err, top_n_fix, exec_time = \
            evaluate_corrector(correctorName, corrector, original_sentences, errored_sentences, max_words)
        results[correctorName] = errors_rate, fix_rate, broken, top_n_err, top_n_fix, exec_time

    print(
        '\n[info] %12s %8s  %8s  %8s  %8s  %8s  %8s' % ('', 'errRate', 'fixRate', 'broken', 'topNerr', 'topNfix',
                                                        'time'))
    for k, _ in sorted(results.items(), key=lambda x: x[1]):
        print('[info] %10s  %8.2f%% %8.2f%% %8.2f%% %8.2f%% %8.2f%% %8.2fs' %
              (k,
               100.0 * results[k][0],
               100.0 * results[k][1],
               100.0 * results[k][2],
               100.0 * results[k][3],
               100.0 * results[k][4],
               results[k][5]))


if __name__ == '__main__':
    main()
