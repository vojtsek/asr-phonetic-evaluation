#! /usr/bin/env python2
from flask import Flask, request, render_template, send_file
import subprocess
import os
import io
import json
import pandas as pd

app = Flask(__name__)
app.debug = True

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    wloc = 'tmp.wav'
    os.remove(wloc)
    wavfile = request.files['wavfile']
    wavfile.save(wloc)
    n = request.form.get('n')
    proc = subprocess.Popen(['./decode_multiple_hypothesis.py', '--wav', wloc, '-n', n], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hypotheses = []
    stdout, stderr = proc.communicate()
    print(stderr.decode())
    for hyp in stdout.decode().split('\n'):
        if len(hyp) < 1:
            continue
        hypotheses.append(hyp)
    return str(hypotheses)
    
@app.route('/transcribe', methods=['POST'])
def transcribe():
    wloc = 'tmp.wav'
    os.remove(wloc)
    wavfile = request.files['wavfile']
    wavfile.save(wloc)
    n = request.values.get('n')
    wc = request.values.get('wc')
    cmd = ['./decode_multiple_hypothesis.py', '--wav', wloc, '-n', n]
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

    return json.dumps(hypothesis)

@app.route('/synthesize', methods=['POST'])
def synth():
    trn = request.values.get('trn')
    ssmlfile = 'in.ssml'
    ofile = 'synth.wav'
    ipa_map = pd.read_csv('ipa_map.tsv', sep='\t', header=None)
    if os.path.exists(ofile):
        os.remove(ofile)
    create_SSML(trn, ssmlfile, ipa_map)
    synthesize(ssmlfile, ofile)
    return send_file(io.BytesIO(open(ofile, 'rb').read()), attachment_filename=ofile, mimetype='audio/wav')

def ipa_lookup(ipa_map, phoneme):
    # todo: employ information from numbers
    prefix = ''
    stress = phoneme[-1]
    if stress.isdigit():
        phoneme = phoneme[:-1]
    return prefix + ipa_map[ipa_map[0] == phoneme][1].values[0].strip()

def create_SSML(trn, ssmlfile, ipa_map):
    def wrap(ph):
        ph = ipa_lookup(ipa_map, ph)
        return '\t<phoneme alphabet="ipa" ph="{}"> {} </phoneme>\n'.format(ph, ph)

    with open(ssmlfile, 'w') as f:
        f.write('<s>\n')
        f.write(''.join(list(map(lambda ph: wrap(ph), trn.split()))))
        f.write('</s>')

def synthesize(ssmlfile, ofile):
    subprocess.call(['./txt2wav.py', ssmlfile, ofile])
