#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from alex_asr import Decoder
from alex_asr.utils import lattice_to_nbest
from transcribe import process_utt
import wave, struct, os
import sys

def join_utterance(decoder, word_ids):
    return (" ".join(map(decoder.get_word, word_ids)))

def decode(wav_name, model_dir):
    gold_trn = open(wav_name + '.trn').read()
    pcm = wave.open(wav_name)

    decoder = Decoder(model_dir)
    frames = pcm.readframes(pcm.getnframes())
    decoder.accept_audio(frames)
    decoder.decode(pcm.getnframes())
    decoder.input_finished()
    n = int(sys.argv[2])
    if n < 2:
        prob, word_ids = decoder.get_best_path()
        print(process_utt('', '', join_utterance(decoder, word_ids), False, ' ', True).strip())
    lkl, lat = decoder.get_lattice()
    for lik, word_ids in lattice_to_nbest(lat, n):
        print(process_utt('', '', join_utterance(decoder, word_ids), False, ' ', True).strip())


if __name__ == "__main__":

    wav_name = sys.argv[1]

    model_dir = '/home/vojta/improve/asr/demo-alex-asr-with-pretrained-model/alex_asr_tri6b_chain_9_3WER_test_clean'
    decode(wav_name, model_dir)
