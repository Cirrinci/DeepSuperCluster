from __future__ import print_function
import ROOT as R 
R.gROOT.SetBatch(True)
#R.PyConfig.IgnoreCommandLineOptions = True

import sys 
import os
from tqdm import tqdm
from collections import defaultdict
from itertools import islice, chain
from numpy import mean
from array import array
from math import sqrt
from pprint import pprint as pp
import numpy as np
import argparse
import pickle
import pandas as pd
import windows_creator
'''
This script analyse the overlapping of two caloparticles
'''

parser = argparse.ArgumentParser()
parser.add_argument("-i","--inputfile", type=str, help="inputfile", required=True)
parser.add_argument("-o","--outputfile", type=str, help="outputfile", default="clusters_data.pkl")
parser.add_argument("-n","--nevents", type=int,nargs="+", help="n events iterator", required=False)
parser.add_argument("-a","--assoc-strategy", type=str, help="Association strategy", default="sim_fraction_min1")
parser.add_argument("-d","--debug", action="store_true",  help="debug", default=False)
parser.add_argument("--weta", type=float, nargs=2,  help="Window eta widths (barrel,endcap)", default=[0.3,0.3])
parser.add_argument("--wphi", type=float, nargs=2, help="Window phi widths (barrel, endcap)", default=[0.7,0.7])
parser.add_argument("--maxnocalow", type=int,  help="Number of no calo window per event", default=15)
args = parser.parse_args()

debug = args.debug
nocalowNmax = args.maxnocalow

f = R.TFile(args.inputfile);
tree = f.Get("recosimdumper/caloTree")

pbar = tqdm(total=tree.GetEntries())


if args.nevents and len(args.nevents) >= 1:
    nevent = args.nevents[0]
    if len(args.nevents) == 2:
        nevent2 = args.nevents[1]
    else:
        nevent2 = nevent+1
    tree = islice(tree, nevent, nevent2)



# maximum baffo
# Dictionary for iz
window_eta = { 0: args.weta[0], 1: args.weta[1], -1: args.weta[1] }
window_phi = { 0: args.wphi[0], 1: args.wphi[1], -1: args.wphi[1] }

totevents = 0
 
energies_maps = []
metadata = []
clusters_masks = []

for iev, event in enumerate(tree):
    totevents+=1
    pbar.update()
    print ('---', iev)
    # if iev % 10 == 0: print(".",end="")
    windows_event, clusters_event = windows_creator.get_windows(event, 
                                window_eta, window_phi, args.maxnocalow, args.assoc_strategy, args.debug )

    clusters_masks += clusters_event
        
# results = np.array(energies_maps)
# meta= pd.DataFrame(metadata)

#results_nocalo = np.array(energies_maps_nocalo)
#np.save("data_calo.npy", results)

#meta.to_csv("metadata_windows.csv", index=False)
#np.save("data_nocalo.npy", results_nocalo)

#pickle.dump(clusters_masks, open("clusters_masks.pkl", "wb"))

df_cl = pd.DataFrame(clusters_masks) 

print(df_cl)
pickle.dump(df_cl, open(args.outputfile, "wb"))
