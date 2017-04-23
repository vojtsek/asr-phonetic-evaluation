#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from alex_asr import Decoder
from alex_asr.utils import lattice_to_nbest, lattice_to_nbest_word_confidence
from transcribe import process_utt
import wave, struct, os
import sys
import argparse

def join_utterance(decoder, word_ids):
    return ' '.join(map(decoder.get_word, word_ids))

def make_hyp(decoder, word_ids):
    hyp = process_utt('', '', join_utterance(decoder, word_ids), False, ' ', True).strip()
    return hyp

def get_contribs_at_position(pos, contribs):
    ph_contribs = {}
    for hyp in contribs:
        hyp = hyp[pos]
        try:
            ph_contribs[hyp[1]] += hyp[0]
        except:
            ph_contribs[hyp[1]] = hyp[0]
    return ph_contribs

def get_most_frequent(ph_dict):
    return sorted(ph_dict.items(), key=lambda x: x[1])[0][0]


def get_most_frequent_path(ph_contribs):
    path = []
    for ph_dict in ph_contribs:
        ph = get_most_frequent(ph_dict)
        path.append(ph)
    return path

def decode(wav_name, model_dir, n, word_conf=False):
    pcm = wave.open(wav_name)

    decoder = Decoder(model_dir)
    frames = pcm.readframes(pcm.getnframes())
    decoder.accept_audio(frames)
    decoder.decode(pcm.getnframes())
    decoder.input_finished()
    N = max(2, n) # nasty hack since for n=1 the nbest does not work
    lkl, lat = decoder.get_lattice()
    p, word_ids = decoder.get_best_path()
# currently align by the best utterance
    best_words = process_utt('', '', join_utterance(decoder, word_ids), False, ' SIL ', True).strip()
    nbest = lattice_to_nbest_word_confidence(lat, N) if word_conf else lattice_to_nbest(lat, N)
    ph_contribs = []
    overall_contribs = []
    for lik, word_ids in nbest:
        # print(lik)
        words = process_utt('', '', join_utterance(decoder, word_ids), False, ' SIL ', True).strip()
        words = filter(lambda x: x != ' ', words.split())
        last = 0
        word_contributions = []
        for w,c in zip(words, lik):
            word_contributions.append(c - last)
            last = c
        words_with_contribs = zip(word_contributions, words)
        print(words_with_contribs)
        overall_contribs.append(words_with_contribs)
        if n == 1:
# TODO: assert likelihod is the same as the get_best()
            break
    best_contribs = overall_contribs[0]
    for pos, ph in enumerate(map(lambda x: x[1], best_contribs)):
        ph_contribs.append(get_contribs_at_position(pos, overall_contribs))
    # print(get_most_frequent_path(ph_contribs))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--wav', help='path to the wav file to be decoced', required=True)
    parser.add_argument('-n', help='number of hypothesis to get', default=1, type=int)
    parser.add_argument('--word_conf', help='Whether show confidence at world level', action='store_true')
    args = parser.parse_args()
    wav_name = args.wav
    n = args.n
    word_conf = args.word_conf

    model_dir = '/home/vojta/improve/asr/demo-alex-asr-with-pretrained-model/alex_asr_tri6b_chain_9_3WER_test_clean'
    decode(wav_name, model_dir, n, word_conf)
