#! /usr/bin/env python3
import glob
import os
import sys
import numpy as np
import subprocess
import pickle
import editdistance as ed


def obtain_trn(line, rec):
    orig = ''
    with open('{}/{}.wav.trn'.format(trndir, rec), 'r') as fi:
        line = fi.read().split()
    with open('processed.txt', 'w') as fo:
        for w in line:
            orig += w + ' '
            fo.write('{}\n'.format(w.upper()))

    proc = subprocess.Popen(['g2p.py', '--model', 'g2p-model-2', '--apply', 'processed.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    transcription = ''
    for trn in proc.communicate()[0].decode().split('\n'):
        if len(trn) == 0:
            continue
        transcription += (trn.split('\t')[1]) + ' '
    return transcription, orig

def get_hypothesis_list(wavdir, rec, n=1):
    proc = subprocess.Popen(['./decode_multiple_hypothesis.py', '--wav', "{}/{}.wav".format(wavdir, rec), '-n', str(n)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hypotheses = []
    odd = False
    for hyp in proc.communicate()[0].decode().split('\n'):
        odd = not odd
        if odd or (len(hyp) < 1):
            continue
        hypotheses.append(hyp)
    return hypotheses

def prepare_data(transcriptions, hypothesis, hyp_file, gold_file, blank_default):
    counter = 0
    for hyp_list, trn in zip(hypothesis, transcriptions):
        counter += 1
        for i, hypotheses in enumerate(hyp_list):
            with open(hyp_file + "." + str(i), "a") as f:
                f.write("{} ({})\n".format(hypotheses, counter))
        with open(gold_file, "a") as f:
            f.write("{} ({})\n".format(trn, counter))

def eval_pra_file(pra, best_dict, idx):
    with open(pra, 'r') as f:
        hyp_len = 0
        for line in f:
            if line.startswith('id:'):
                uid = line.split()[1].lstrip('(').rstrip(')')
            if line.startswith('REF:'):
                splitted = line.split()[1:]
                ref_len = len([sp for sp in splitted if len(sp.strip('*')) > 0])
            if line.startswith('HYP:'):
                splitted = line.split()[1:]
                hyp_len = len([sp for sp in splitted if len(sp.strip('*')) > 0])
            if line.startswith('Eval'):
                splitted = line.split()[1:]
                no_s = len([sp for sp in splitted if sp == 'S'])
                no_i = len([sp for sp in splitted if sp == 'I'])
                no_d = len([sp for sp in splitted if sp == 'D'])
                wer = no_d + no_i + no_s
                try:
                    if wer < best_dict[uid][0]:
                        best_dict[uid] = (wer, ref_len, idx)
                except:
                    best_dict[uid] = (wer, ref_len, idx)

def eval_hypothesis_list(transcriptions, hypotheses, n=1, oracle=True):
    ref = 'trns.lst'
    base_hyp = 'hypothesis.lst'
    SCTK_PATH = os.environ.get('SCTK_PATH', 'sctk/bin')
    prepare_data(transcriptions, hypotheses, base_hyp, ref, '')
    pra_files = []
    for i in range(n):
        hyp = base_hyp + '.' + str(i)
        cmd = ["{}/sclite".format(SCTK_PATH), "-r", ref, "-h", hyp, "-i", "rm", "-o", "pra", "sum"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate(b"")
        rc = p.returncode
        if rc != 0:
            print('Error running sclite')
        else:
            pra_files.append(hyp + '.pra')
    return pra_files
 
if __name__ == '__main__':
    if len(sys.argv) == 2:
        n = int(sys.argv[1])
        with open('results_{}_best.dump'.format(n), 'rb') as f:
            best_dict = pickle.load(f)
            idxs = list(map(lambda x: x[2], best_dict.values()))
            for i in range(n):
                bd_values_i = [item[0] for item in best_dict.values() if item[2] == i]
                bd_lens_i = [item[1] for item in best_dict.values() if item[2] == i]
                if len(bd_lens_i) == 0:
                    continue
                print("Hypotheses {} PER: {}".format(i, sum(bd_values_i) / sum(bd_lens_i)))
            pers = []
            print(np.bincount(idxs))

    else:
        wavdir = sys.argv[1]
        trndir = sys.argv[2]
        n = int(sys.argv[3])
        transcriptions = []
        hypothesis_lst = []
        best = dict()
#    with open('phonetic-trns.all', 'w') as of:
#        with open('transcriptions.all', 'r') as f:
#            for line in f:
#                sp = line.split()
#                trn, orig = obtain_trn(' '.join(sp[:-1]), '')
#                of.write('{} {}\n'.format(trn, sp[-1]))

        for rec in glob.glob('{}/*.wav'.format(wavdir)):
            print('Recognizing {}'.format(rec))
            rec = '.'.join(os.path.basename(rec).split('.')[:-1])
            transcription, orig = obtain_trn(trndir, rec)
            hypothesis = get_hypothesis_list(wavdir, rec, n)
            hypothesis_lst.append(hypothesis)
            transcriptions.append(transcription)

        pra_files = eval_hypothesis_list(transcriptions, hypothesis_lst, n)
        for pf in pra_files:
            idx = int(pf.split('.')[-2])
            eval_pra_file(pf, best, idx)
        
        pickle.dump(best, open('results_{}_best.dump'.format(n), 'wb'))

        pers = sum(map(lambda x: int(x[1][0]), best.items()))
        hyp_lens = sum(map(lambda x: int(x[1][1]), best.items()))
        overall_per = pers / hyp_lens
        print('Overall PER is: {}%'.format(overall_per * 100))

#    print ('"{}:{}"; WER:{}, {}'.format(orig, transcription, wer, best))
