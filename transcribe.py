#! /usr/bin/env python3
"""
    Transcribe phonetic transcriptions containing position-specific phonemes (AA_I, AA_E,..) without these marks
"""
import sys
import glob
import re
import os

gid = 0
def tr_phone(ph, strip_stress):
    ph = ph[:-2]
    if strip_stress:
        return ph.rstrip('0123')
    return ph

def process_utt(trn, uid, utt, sctk=True, sp_char='__', strip_stress=False):
    result = ''
    for ph in utt.split():
        if ph == 'SIL':
            #if sctk:
            #    continue
            result = result[:-1] + sp_char
        else:
            result += tr_phone(ph, strip_stress) + ' '
    if sctk:
        global gid
        gid += 1
        if sctk:
            with open('transcriptions.all', 'a') as f:
                f.write('{} ({})\n'.format(trn, gid))
        return "{} ({})".format(result, gid)
    return('{} {}'.format(uid, result))

def process_log(fn, trns, sctk):
    """
    processes kaldi log in the form:
    1111-2222-333 this is transcription
    """
    with open(fn, 'r') as f:
        with open('decoded.out', 'a') as of:
            for line in f:
                mtch = re.match('^(\d*-\d*-\d*) (.*)', line)
                if mtch is not None:
                    processed = process_utt(trns[mtch.group(1)], mtch.group(1), mtch.group(2), sctk)
                    of.write(processed + '\n')

if __name__ == '__main__':
    logs = sys.argv[1]
    trnfile = sys.argv[2]

    trns = dict()
    with open(trnfile, 'r') as f:
        for line in f:
            splitted = line.split()
            trns[splitted[0]] = ' '.join(splitted[1:])

    if logs.endswith('.log'):
        process_log(logs, trns)
    else:
        for fn in glob.glob('{}/*.log'.format(logs)):
            process_log(fn, trns, True)
