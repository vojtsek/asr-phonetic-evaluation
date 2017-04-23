#! /usr/bin/env python2
import subprocess
import os
import io
import json
import pandas as pd
import ast

from flask import Flask, request, render_template, send_file

from utils import create_transcription_json, create_SSML, ipa_lookup, synthesize, process_tts

app = Flask(__name__)
app.debug = True

def do_alignments(d):
    resfile = 'results-ctm.aligned'
    os.remove(resfile)
    cmd = ['./create_ctm.sh', d, '/scratch/experiments/oplatek-experiments/oplatek-kaldi-librispeech/egs/librispeech/s5/data/lang', '/scratch/experiments/oplatek-experiments/oplatek-kaldi-librispeech/egs/librispeech/s5/exp/tri2b']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if os.path.exists(resfile):
        with open(resfile, 'r') as f:
            phonemes = []
            for line in f:
                uid, ch, begin, dur, ph = line.split()
                begin = float(begin)
                dur = float(dur)
                phonemes.append((begin, begin+dur, ph))
    return phonemes

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    wloc = 'tmp.wav'
    if os.path.exists(wloc):
        os.remove(wloc)
    wavfile = request.files['wavfile']
    wavfile.save(wloc)
    n = request.values.get('n')
    wc = request.values.get('wc')
    cmd = ['./test-phonetic.py', '--wav', wloc, '-n', n]
    if wc is not None and wc:
        cmd.append('--word_conf')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hypothesis = []
    stdout, stderr = proc.communicate()
    for hyp in stdout.decode().split('\n'):
        if len(hyp) < 1:
            continue
        hypothesis.append(ast.literal_eval(hyp))
    
    page = ''
    for hyp in hypothesis:
        def mapf(ph):
            mxm = max(map(lambda x: x[0], hyp))
            mnm = min(map(lambda x: x[0], hyp))
            return colorise(ph, mxm, mnm)

        page = page + ''.join(list(map(mapf, hyp))) + '<br />'
    return page

@app.route('/transcribe', methods=['POST'])
def transcribe():
    wavdir = 'webdata'
    wavloc = wavdir + '/tmp.wav'
    if not os.path.isdir(wavdir):
        os.mkdir(wavdir)
    if os.path.exists(wavloc):
        os.remove(wavloc)
    wavfile = request.files['wavfile']
    wavfile.save(wavloc)
    n = request.values.get('n')
    wc = request.values.get('wc')
    hyp_list = create_transcription_json(wavloc, n, wc)
    with open('trns.out', 'w') as f:
        for trn in hyp_list:
            f.write(trn['transcription'] + '\n')
#    all_ali = []
#    for i, trn in enumerate(hyp_list):
#        with open(wavloc + '.trn', 'w') as f:
#            print(trn['transcription'])
#            filtered = ' '.join(list(filter(lambda x: x != 'SIL', trn['transcription'].split())))
#            f.write(filtered.upper())
#        all_ali.append(do_alignments(wavdir))
#    for ali in all_ali:
#        print(ali)
    return json.dumps(hyp_list)

@app.route('/synthesize', methods=['POST'])
def synth():
    trn = request.values.get('trn')
    ofile = 'synth.wav'
    process_tts(trn, ofile)
    return send_file(io.BytesIO(open(ofile, 'rb').read()), attachment_filename=ofile, mimetype='audio/wav')

