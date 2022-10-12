#!/bin/sh

python condor_awkward_dataset.py -i /eos/user/r/rdfexp/ecal/cluster/output_deepcluster_dumper/windows_data/gammas/ndjson_2022_v3 \
       -o /eos/user/r/rdfexp/ecal/cluster/output_deepcluster_dumper/windows_data/gammas/awkward_2022v10_onlycalomatched \
       -q espresso -nfg 10 -f features_definition.json -cf condor_awk_gammas --flavour 22

python condor_awkward_dataset.py -i /eos/user/r/rdfexp/ecal/cluster/output_deepcluster_dumper/windows_data/electrons/ndjson_2022_v3 \
       -o /eos/user/r/rdfexp/ecal/cluster/output_deepcluster_dumper/windows_data/electrons/awkward_2022v10_onlycalomatched\
       -q espresso -nfg 10 -f features_definition.json -cf condor_awk_electrons --flavour 11
