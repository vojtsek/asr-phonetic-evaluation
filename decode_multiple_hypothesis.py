#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from alex_asr import Decoder
from alex_asr.utils import lattice_to_nbest, lattice_to_nbest_word_confidence
from transcribe import process_utt
import wave, struct, os
import sys
import argparse

def join_utterance(decoder, word_ids):
    return (" ".join(map(decoder.get_word, word_ids)))

def make_hyp(decoder, word_ids):
    hyp = process_utt('', '', join_utterance(decoder, word_ids), False, ' ', True).strip()
    return hyp

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
    nbest = lattice_to_nbest_word_confidence(lat, N) if word_conf else lattice_to_nbest(lat, N)
    for lik, word_ids in nbest:
        #print(lik)
        words = process_utt('', '', join_utterance(decoder, word_ids), False, ' ', True).strip()
        print(words)
        if n == 1:
# TODO: assert likelihod is the same as the get_best()
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--wav', help='path to the wav file to be decoced', required=True)
    parser.add_argument('-n', help='number of hypothesis to get', default=1, type=int)
    parser.add_argument('--word_conf', help='Whether show confidence at world level', action='store_true')
    args = parser.parse_args()
    wav_name = args.wav
    n = args.n
    word_conf = args.word_conf

    model_dir = '/scratch/vojta-code/chain-model-phones'
    model_dir_new = '/scratch/vojta-code/chain-model-phones-0120'

    decode(wav_name, model_dir_new, n, word_conf)
