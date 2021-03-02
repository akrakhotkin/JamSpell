import os
import pytest

import jamspell
from evaluate_jamspell import generate_dataset
from evaluate_jamspell.evaluate import evaluate_jamspell


def remove_file(file_name):
    try:
        os.remove(file_name)
    except OSError:
        pass


TEMP_MODEL = 'temp_model.bin'
TEMP_SPELL = 'temp_model.bin.spell'
TEMP = 'temp'
TEMP_TEST = TEMP + '_test.txt'
TEMP_TRAIN = TEMP + '_train.txt'
TEST_DATA = 'test_data/'


def teardown_module(module):
    remove_file(TEMP_MODEL)
    remove_file(TEMP_SPELL)
    remove_file(TEMP_TEST)
    remove_file(TEMP_TRAIN)


def train_lang_model(train_text, alphabet_file, model_file):
    corrector = jamspell.TSpellCorrector()
    corrector.TrainLangModel(train_text, alphabet_file, model_file)


@pytest.mark.parametrize('source_file,alphabet_file,expected', [
    ('sherlockholmes.txt', 'alphabet_en.txt', (0.04538662682106836, 0.6987951807228916, 0.014246804944479363,
                                               0.013821441912588718, 0.76592082616179)),
    ('kapitanskaya_dochka.txt', 'alphabet_ru.txt', (0.12330535829567463, 0.391304347826087, 0.03866565579984837,
                                                    0.05358295674628793, 0.4391304347826087)),
])
def test_evaluation(source_file, alphabet_file, expected):
    alphabet_file = TEST_DATA + alphabet_file
    generate_dataset.generate_dataset_txt(TEST_DATA + source_file, TEMP)
    train_lang_model(TEMP_TRAIN, alphabet_file, TEMP_MODEL)
    results = evaluate_jamspell(TEMP_MODEL, TEMP_TEST, alphabet_file)
    assert results == expected
