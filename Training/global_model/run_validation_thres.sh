#!/bin/sh

python run_validation_dataset_enregr_thres.py -d v10 --model-dir /eos/user/d/dvalsecc/www/ECAL/Clustering/DeepCluster/models_archive/gcn_models/gcn_models_SA_v11/run_01/en_regr/run_01 \
   --model-weights weights.best.hdf5 -o /eos/user/d/dvalsecc/www/ECAL/Clustering/DeepCluster/models_archive/gcn_models/gcn_models_SA_v11/run_01/en_regr/run_01/validation_data_thrs -n 600000 -b 300
