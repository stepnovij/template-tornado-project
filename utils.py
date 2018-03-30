import hashlib
import random
import string
import logging
import time

import nltk
from nltk.translate.bleu_score import SmoothingFunction
from multiprocessing import Pool

LOGGING_FORMAT = '%(asctime)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)


def generate_hash(name):
    salt = ''.join([random.choice(string.printable) for i in range(16)])
    sha = hashlib.md5((str(name) + str(time.time()) + str(salt)).encode('utf8'))
    return sha.hexdigest()


def split(arr, size):
    arrs = []
    while len(arr) > size:
        pice = arr[:size]
        arrs.append(pice)
        arr = arr[size:]
    arrs.append(arr)
    return arrs


def run_single_corpus_bleu(pair):
    """
    >>> hyp1 = "It is a guide to action which ensures that the military always obeys the commands of the party"
    >>> ref1 = "It is a guide to action that ensures that the military will forever heed Party commands"
    >>> hyp2 = "he read the book because he was interested in world history"
    >>> ref2 = "he was interested in world history because he read the book"

    >>> score_translation([ref1, ref2], [hyp1, hyp2])
    0.1523009076658375

    >>> score_translation([ref1, ref2], [ref1, ref2])
    0.1523009076658375
    """
    list_of_references, hypotheses = pair
    return nltk.translate.bleu_score.corpus_bleu(list_of_references, hypotheses,
                                                 smoothing_function=SmoothingFunction().method4)


def score_translation(references, hypothesis, type_='bleu'):
    """
    :type references: list
    :type hypothesis: list
    :type type_: str
    :rtype: float
    """
    list_of_hypotheses = [input_sentence.split(' ') for input_sentence in hypothesis]
    list_of_references = [ref_sentence.split(' ') for ref_sentence in references]

    if not type_ == 'bleu':
        raise Exception('Not acceptable type')

    logging.info('starting score calculation: %s', type_)
    #
    number_threshold = 40
    # split in pairs if size more than number_threshold
    list_of_sublists_ref = split(list_of_references, number_threshold)
    list_of_sublists_hyp = split(list_of_hypotheses, number_threshold)
    pairs = zip(list_of_sublists_ref, list_of_sublists_hyp)

    # run in parallel
    with Pool() as pool:
        result = pool.map(run_single_corpus_bleu, pairs)
    bleu = sum(result)/len(result)
    #
    logging.info('finishing score calculation: %s', type_)

    return bleu
