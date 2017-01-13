#! /usr/bin/env python2
from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__)
app.debug = True

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/uploader', methods=['POST'])
def transcribe():
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
