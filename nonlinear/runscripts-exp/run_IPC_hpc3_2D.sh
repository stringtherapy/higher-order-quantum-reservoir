#!/usr/bin/bash
# Script to calculate IPC from hpc3
# Varying with disorder strength W in dynamical phase transition model
# Version 2022-06-07
export OMP_NUM_THREADS=1

EXE=../source/runIPC_2D.py
BINPLOT=../postprocess/plot_IPC_2D.py

BASE='rand_input_2001000'
#BASE='rand_input'

PARENT=../../../data/hqrc/$BASE/IPC_2D_v20220614
INPUT=../data/$BASE.txt

#T=2000000
T=1000000
#T=1000

WD=50
VAR=7
DEG=7
DELAYS='0,100,50,50,20,20,10,10'
#DELAYS='0,20,20,20,20,20,10,10'
#DELAYS='0,100,50,50,20'

#
V='1'
TAUS='10.0'
NSPINS=6
NPROC=111
QR=1

THRES=0.0
DYNAMIC='phase_trans'
CAPA=6
CB=1
OP='Z'
TP=5

FRS='XXX'
for SEED in 0
do
LBS=IPC_op_$OP\_tp_$TP\_cb_$CB\_seed_$SEED
SAVE=$PARENT\/$LBS
FRS=$FRS,$LBS

python $EXE --rho 1 --input_file $INPUT --combine_input $CB --type_input $TP --type_op $OP --nqrc $QR --nproc $NPROC --spins $NSPINS --seed $SEED --dynamic $DYNAMIC --deg_delays $DELAYS --thres $THRES --virtuals $V --length $T --max_deg $DEG --max_window $WD --max_num_var $VAR --savedir $SAVE
done


P=mdeg_$DEG\_mvar_$VAR

for THRES in 0.0 5e-5
do
python $BINPLOT --solver 'linear_pinv_' --parent $PARENT --folders $FRS --T $T --thres $THRES --nqrc $QR --dynamic $DYNAMIC --virtuals $V --taus $TAUS --nspins $NSPINS --keystr $P
done


