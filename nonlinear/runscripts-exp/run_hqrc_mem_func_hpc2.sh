#!/usr/bin/bash
# Script to calculate memory function
# Version 2022-06-06
export OMP_NUM_THREADS=1

BIN=../source/mf_hqrc_Ws.py
N=10

BASE='rand_input_101000'

SAVE=../../../data/hqrc/$BASE/mem_v20220606
TASK=../data/$BASE.txt

QR=5
PROC=101
SOLVER='ridge_pinv'
#SOLVER='linear_pinv'

LOGWS=\'-2.0,-1.8,-1.6,-1.4,-1.2,-1.0,-0.8,-0.6,-0.4,-0.2,0.0\' # The parameters for W is 10**x for W in LOGWS

MIND=0
MAXD=200
INT=1
CB=1
TP=5
OP='X'

TRAIN=3000
VAL=1000
BUF=1000

for gamma in 1.0
do
for V in 1
do
python $BIN --trainlen $TRAIN --vallen $VAL --buffer $BUF --type_op $OP --type_input $TP --combine_input $CB  --solver $SOLVER --log_Ws $LOGWS --task $TASK --nqrc $QR --strength $gamma --virtuals $V --ntrials $N --nproc $PROC --mind $MIND --maxd $MAXD --interval $INT --savedir $SAVE
done
done
