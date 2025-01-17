#!/bin/bash -e

echo "Starting"
source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh

echo "Training"
python trainer_awk.py --config $1 --model $2 --name $3
