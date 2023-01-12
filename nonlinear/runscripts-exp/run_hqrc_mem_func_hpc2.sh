#!/usr/bin/bash
# Script to calculate memory function
# Version 2022-06-08
export OMP_NUM_THREADS=1

BIN=../source/mf_hqrc_Ws.py
N=10

BASE='rand_input_2001000'

SAVE=../../../data/hqrc/$BASE/mem_v20220608
TASK=../data/$BASE.txt

QR=5
PROC=101
SOLVER='ridge_pinv'
#SOLVER='linear_pinv'

#LOGWS=\'-2.0,-1.8,-1.6,-1.4,-1.2,-1.0,-0.8,-0.6,-0.4,-0.2,0.0\' # The parameters for W is 10**x for W in LOGWS
#LOGWS=\'-1.9,-1.7,-1.5,-1.3,-1.1,-0.9,-0.7,-0.5,-0.3,-0.1\' # The parameters for W is 10**x for W in LOGWS
#LOGWS=\'0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0\' # The parameters for W is 10**x for W in LOGWS
LOGWS=\'-2.0,-1.8,-1.6,-1.4,-1.2,-1.0,-0.8,-0.6,-0.4,-0.2,0.0,0.2,0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0\'
MIND=0
MAXD=200
INT=1
CB=1
TP=5
OP='Z'

TRAIN=3000
VAL=1000
BUF=1000
RHO=1 #Version 2022-06-08 should be 1 to evaluate the fluctiation when sepcifing the initial density matrix

for gamma in 1.0 0.0
do
for V in 1
do
python $BIN --rho $RHO --trainlen $TRAIN --vallen $VAL --buffer $BUF --type_op $OP --type_input $TP --combine_input $CB  --solver $SOLVER --log_Ws $LOGWS --task $TASK --nqrc $QR --strength $gamma --virtuals $V --ntrials $N --nproc $PROC --mind $MIND --maxd $MAXD --interval $INT --savedir $SAVE
done
done
