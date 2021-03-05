#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import random
import os
import argparse
import xml.sax

from collections import defaultdict

from langdetect import detect

RANDOM_SEED = 42
TRAIN_TEST_SPLIT = 0.95
LANG_DETECT_FRAGMENT_SIZE = 2000


def save_sentences(sentences, file_name):
    with codecs.open(file_name, 'w', 'utf-8') as f:
        for s in sentences:
            f.write(s)
            f.write('\n')


def dir_files_iterator(dir_path):
    for root, directories, filenames in os.walk(dir_path):
        for filename in filenames:
            yield os.path.join(root, filename)


class FB2Handler(xml.sax.handler.ContentHandler):
    def __init__(self, tags_to_exclude):
        xml.sax.handler.ContentHandler.__init__(self)
        self.__tagsToExclude = tags_to_exclude
        self.__counters = defaultdict(int)
        self.__buff = []

    def get_buff(self):
        return ''.join(self.__buff)

    def _may_process(self):
        for counter in self.__counters.values():
            if counter > 0:
                return False
        return True

    def startElement(self, name, attrs):
        if name in self.__tagsToExclude:
            self.__counters[name] += 1

    def endElement(self, name):
        if name in self.__tagsToExclude:
            self.__counters[name] -= 1

    def characters(self, content):
        if self._may_process():
            self.__buff.append(content)


class DataSource(object):
    def __init__(self, path, name, lang=None):
        self.__path = path
        self.__name = name
        self.__lang = lang

    def get_path(self):
        return self.__path

    def get_name(self):
        return self.__name

    def is_match(self, path_to_file):
        return False

    def load_sentences(self, path_to_file, sentences):
        pass

    def check_lang(self, text_fragment):
        if self.__lang is None:
            return True
        if detect(text_fragment) != self.__lang:
            return False
        return True


class LeipzigDataSource(DataSource):
    def __init__(self, path, lang):
        super(LeipzigDataSource, self).__init__(path, 'leipzig', lang)

    def is_match(self, path_to_file):
        return path_to_file.endswith('-sentences.txt')

    def load_sentences(self, path_to_file, sentences):
        with codecs.open(path_to_file, 'r', 'utf-8') as f:
            data = f.read()
            if not self.check_lang(data[:LANG_DETECT_FRAGMENT_SIZE]):
                return
            for line in data.split('\n'):
                if not line:
                    continue
                sentences.append(line.split('\t')[1].strip().lower())


class TxtDataSource(DataSource):
    def __init__(self, path, lang):
        super(TxtDataSource, self).__init__(path, 'txt', lang)

    def is_match(self, path_to_file):
        return path_to_file.endswith('.txt')

    def load_sentences(self, path_to_file, sentences):
        with codecs.open(path_to_file, 'r', 'utf-8') as f:
            for line in f.read().split('\n'):
                line = line.strip().lower()
                if not line:
                    continue
                sentences.append(line)


class FB2DataSource(DataSource):
    def __init__(self, path, lang):
        super(FB2DataSource, self).__init__(path, 'FB2', lang)

    def is_match(self, path_to_file):
        return path_to_file.endswith('.fb2')

    def load_sentences(self, path_to_file, sentences):
        parser = xml.sax.make_parser()
        handler = FB2Handler(['binary'])
        parser.setContentHandler(handler)
        print('[info] loading file', path_to_file)
        with open(path_to_file, 'rb') as f:
            parser.parse(f)
        data = handler.get_buff()
        if not self.check_lang(data[:LANG_DETECT_FRAGMENT_SIZE]):
            print('[info] wrong language')
        for line in data.split('\n'):
            line = line.strip().lower()
            if not line:
                continue
            sentences.append(line)


def generate_dataset_txt(in_file, out_file):
    source = TxtDataSource(in_file, None)
    sentences = []
    source.load_sentences(in_file, sentences)
    assert sentences
    process_sentences(sentences, out_file)


def process_sentences(sentences, out_file):
    print('[info] removing duplicates')

    sentences = list(set(sentences))

    print('[info] %d left' % len(sentences))
    print('[info] shuffling')

    random.seed(RANDOM_SEED)
    random.shuffle(sentences)

    total = len(sentences)
    train_half = int(total * TRAIN_TEST_SPLIT)
    train_sentences = sentences[:train_half]
    test_sentences = sentences[train_half:]

    print('[info] saving train set')
    save_sentences(train_sentences, out_file + '_train.txt')

    print('[info] saving test set')
    save_sentences(test_sentences, out_file + '_test.txt')

    print('[info] done')


def main():
    parser = argparse.ArgumentParser(description='dataset generator')
    parser.add_argument('out_file', type=str, help='will be created out_file_train and out_file_test')
    parser.add_argument('-lz', '--leipzig', type=str, help='path to file or dir with Leipzig Corpora files')
    parser.add_argument('-fb2', '--fb2', type=str, help='path to file or dir with files in FB2 format')
    parser.add_argument('-txt', '--txt', type=str, help='path to file or dir with utf-8 txt files')
    parser.add_argument('-lng', '--language', type=str, help='filter by content language')
    args = parser.parse_args()

    lang = None
    if args.language:
        lang = args.language

    data_sources = []
    if args.leipzig:
        data_sources.append(LeipzigDataSource(args.leipzig, lang))
    if args.fb2:
        data_sources.append(FB2DataSource(args.fb2, lang))
    if args.txt:
        data_sources.append(TxtDataSource(args.txt, lang))

    if not data_sources:
        raise Exception('specify at least single data source')

    sentences = []
    for dataSource in data_sources:
        print('[info] loading %s collection' % dataSource.get_name())
        path = dataSource.get_path()
        paths = [path] if os.path.isfile(path) else dir_files_iterator(path)
        for filePath in paths:
            if dataSource.is_match(filePath):
                dataSource.load_sentences(filePath, sentences)

    print('[info] loaded %d sentences' % len(sentences))
    if not sentences:
        print('[error] no sentences loaded')
        return

    process_sentences(sentences, args.out_file)


if __name__ == '__main__':
    main()
