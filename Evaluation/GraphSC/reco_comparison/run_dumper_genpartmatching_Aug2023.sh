#!/bin/sh -e
ver=$1
options=" --reco-collection genparticle"


basedir="/eos/cms/store/group/dpg_ecal/alca_ecalcalib/bmarzocc/Clustering/"
outdir="/eos/user/r/rdfexp/ecal/cluster/output_deepcluster_dumper/reco_comparison/genmatching_efficiency_studies/"


python condor_reco_dumper.py -i ${basedir}/ \
       -o ${outdir}electrons_genmatching/DeepSC_algoA_235noise_UL18_v${ver}/ -a sim_fraction --wp-file simfraction_electron_235_UL18.json -nfg 40 -q espresso --compress ${options} -cf condor_dumper_genmatching_ele_deepsc_UL18

cd condor_dumper_genmatching_ele_deepsc_UL18;
condor_submit condor_job.txt
cd ..


python condor_reco_dumper.py -i ${basedir}/ \
       -o ${outdir}electrons_genmatching/Mustache_235noise_UL18_v${ver}/ -a sim_fraction --wp-file simfraction_electron_235_UL18.json -nfg 40 -q espresso --compress ${options} -cf condor_dumper_genmatching_ele_mustache_UL18

cd condor_dumper_genmatching_ele_mustache_UL18;
condor_submit condor_job.txt
cd ..
