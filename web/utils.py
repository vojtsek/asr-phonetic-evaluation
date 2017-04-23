#! /usr/bin/env python3
import sys
import os
import subprocess
import json
import pandas as pd

def create_transcription_json(inwav, n, wc):
    decoder_path = os.path.abspath(os.path.dirname(__file__))
    cmd = ['{}/decode_multiple_hypothesis.py'.format(decoder_path), '--wav', inwav, '-n', n]
    if wc is not None and wc == 'true':
        cmd.append('--word_conf')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hypothesis = []
    stdout, stderr = proc.communicate()
    odd = False
    confidence = ''
    for line in stdout.decode().split('\n'):
        if len(line) < 1:
            continue
        odd = not odd
        if odd:
            confidence = line
        else:
            hypothesis.append({'confidence': confidence, 'transcription': line})

    return hypothesis

def process_tts(trn, ofile):
    ssmlfile = 'in.ssml'
    ipa_map = pd.read_csv('ipa_map.tsv', sep='\t', header=None)
    if os.path.exists(ofile):
        os.remove(ofile)
    create_SSML(trn, ssmlfile, ipa_map)
    synthesize(ssmlfile, ofile)

def ipa_lookup(ipa_map, phoneme):
    # todo: employ information from numbers
    prefix = ''
    stress = phoneme[-1]
    if stress.isdigit():
        phoneme = phoneme[:-1]
    return prefix + ipa_map[ipa_map[0] == phoneme][1].values[0].strip()

def create_SSML(trn, ssmlfile, ipa_map):
    def wrap(ph):
        if 'SIL' in ph:
            return '<break strength="weak" />'
        ph = ipa_lookup(ipa_map, ph)
        return '\t<phoneme alphabet="ipa" ph="{}"> {} </phoneme>\n'.format(ph, ph)

    with open(ssmlfile, 'w') as f:
        f.write('<s>\n')
        f.write(''.join(list(map(lambda ph: wrap(ph), trn.split()))))
        f.write('</s>')

def colorise(letter, mxm, mnm):
    color = 'green' if letter[0] > 0.005 else 'red'
    return '<span style="color:{0}">{1}</span><span style="color:gray;">&nbsp;({2:.8f})</span>'.format(color, letter[1], letter[0])
    
def synthesize(ssmlfile, ofile):
    subprocess.call(['./txt2wav.py', ssmlfile, ofile])

if __name__ == '__main__':
    infile = sys.argv[1]
    outdir = sys.argv[2]
    with open(outdir + '/' + infile + '.json', 'w') as of:
        of.write(create_transcription_json(infile + '.wav', '5', 'true'))
