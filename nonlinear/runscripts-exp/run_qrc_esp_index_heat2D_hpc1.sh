#!/usr/bin/bash
# Script to view dynamics of the HQRC
export OMP_NUM_THREADS=1

BIN=../source/ESP_index_heat_2D.py
LENGTH=10000
BUFFER=9000

#LENGTH=2000
#BUFFER=1000

TRIALS=10


BASE='rand_input_2001000'
SAVE=../../../data/hqrc/$BASE/esp_2D

#INPUT_FILE=../data/sin_input_T_50.txt
INPUT_FILE=../data/$BASE.txt

QR=1
PROC=111
CONST=0
INT=0.05

GMIN=-2.0
GMAX=2.1
GINT=0.05

OP='Z'


for TP in 5 8 9
do
for RD in 0
do
RSFILE=$SAVE/heat_phase_trans_nqr_1_V_1_tau_10.0_nondiag_2.0_op_X_tp_$TP\_trials_$TRIALS\_rsd_$RD\_esp_id_99_len_$LENGTH.binaryfile

python $BIN --gvmin $GMIN --gvmax $GMAX --ginterval $GINT --type_op $OP  --input_file $INPUT_FILE --randseed $RD --trials $TRIALS --type_input $TP --interval $INT --savedir $SAVE --length $LENGTH --buffer $BUFFER --nqrc $QR --nproc $PROC
#python $BIN --trials $TRIALS --type_input $TP --gvmin $GMIN --gvmax $GMAX --ginterval $GINT --interval $INT --savedir $RSFILE --length $LENGTH --buffer $BUFFER --nqrc $QR --nproc $PROC
done
done