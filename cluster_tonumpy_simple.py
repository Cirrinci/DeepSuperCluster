from __future__ import print_function
import ROOT as R 
R.gROOT.SetBatch(True)
#R.PyConfig.IgnoreCommandLineOptions = True

import sys 
import os
from tqdm import tqdm
from collections import defaultdict
from math import cosh
from itertools import islice, chain
from numpy import mean
from operator import itemgetter, attrgetter
from array import array
from math import sqrt
from pprint import pprint as pp
import numpy as np
import argparse
import pickle
import random
import string
from pprint import pprint
import pandas as pd
'''
This script analyse the overlapping of two caloparticles
'''

parser = argparse.ArgumentParser()
parser.add_argument("-i","--inputfile", type=str, help="inputfile", required=True)
parser.add_argument("-o","--outputfile", type=str, help="outputfile", default="clusters_data.pkl")
parser.add_argument("-n","--nevents", type=int,nargs="+", help="n events iterator", required=False)
parser.add_argument("-d","--debug", action="store_true",  help="debug", default=False)
parser.add_argument("--weta", type=int,  help="Window eta width", default=10)
parser.add_argument("--wphi", type=int,  help="Window phi width", default=20)
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


def DeltaR(phi1, eta1, phi2, eta2):
        dphi = phi1 - phi2
        if dphi > R.TMath.Pi(): dphi -= 2*R.TMath.Pi()
        if dphi < -R.TMath.Pi(): dphi += 2*R.TMath.Pi()
        deta = eta1 - eta2
        deltaR = (deta*deta) + (dphi*dphi)
        return sqrt(deltaR)

def DeltaPhi(phi1, phi2):
    dphi = phi1 - phi2
    if dphi > R.TMath.Pi(): dphi -= 2*R.TMath.Pi()
    if dphi < -R.TMath.Pi(): dphi += 2*R.TMath.Pi()
    return dphi

def transform_ieta(ieta):
    if ieta > 0:  return ieta +84
    elif ieta < 0: return ieta + 85

def iphi_distance(iphiseed, iphi, iz):
    if iz == 0:
        if abs(iphiseed-iphi)<= 180: return iphi-iphiseed
        if iphiseed < iphi:
            return iphi-iphiseed - 360
        else:
            return iphi - iphiseed + 360
    else :
        return iphi - iphiseed

def ieta_distance(ietaseed, ieta, iz):
    if iz == 0:
        return transform_ieta(ieta) - transform_ieta(ietaseed)
    else:
        return ieta-ietaseed


# maximum baffo
window_ieta = args.weta
window_iphi = args.wphi

# Check if a xtal is in the window
def in_window(seed_ieta, seed_iphi, seed_iz, ieta, iphi, iz):
    if seed_iz != iz: return False, (-1,-1)
    ietaw = ieta_distance(seed_ieta,ieta,iz)
    iphiw = iphi_distance(seed_iphi,iphi,iz)
    if abs(ietaw) <= window_ieta and abs(iphiw) <= window_iphi: 
        return True, (ietaw, iphiw)
    else:
        return False,(-1,-1)

# Check if cluster has an hit in the window
def cluster_in_window(window, clhits_ieta, clhits_iphi, clhits_iz):
    for ieta, iphi, iz in zip(clhits_ieta, clhits_iphi, clhits_iz):
        hit_in_wind, (ietaw, iphiw) = in_window(window["seed"][0],window["seed"][1],window["seed"][2],ieta, iphi, iz)
        #print((ieta,iphi,iz), (window["seed"][0],window["seed"][1],window["seed"][2]), ietaw, iphiw)
        if hit_in_wind:
            return True
    return False

totevents = 0
 
energies_maps = []
metadata = []
clusters_masks = []



for iev, event in enumerate(tree):
    totevents+=1
    nocalowN = 0
    windows_index = -1
    clusters_event = []
    pbar.update()
    #print ('---', iev)
    # if iev % 10 == 0: print(".",end="")

    # Branches
    pfCluster_energy = event.pfCluster_energy
    pfCluster_ieta = event.pfCluster_ieta
    pfCluster_iphi = event.pfCluster_iphi
    pfCluster_eta = event.pfCluster_eta
    pfCluster_phi = event.pfCluster_phi
    pfCluster_iz = event.pfCluster_iz

    clhit_ieta = event.pfClusterHit_ieta;
    clhit_iphi = event.pfClusterHit_iphi;
    clhit_iz = event.pfClusterHit_iz;
    clhit_eta = event.pfClusterHit_eta;
    clhit_phi = event.pfClusterHit_phi;
    clhit_energy = event.pfClusterHit_energy;
    clhit_rechitEnergy = event.pfClusterHit_rechitEnergy

    calo_simeta = event.caloParticle_simEta;
    calo_simphi = event.caloParticle_simPhi;
    calo_simenergy = event.caloParticle_simEnergy;

    pfcluster_calo_map = event.pfCluster_sim_fraction_min1_MatchedIndex
    calo_pfcluster_map = event.caloParticle_pfCluster_sim_fraction_min1_MatchedIndex
   
    # map of windows, key=pfCluster seed index
    windows_map = {}
    nonseed_clusters = []
    # 1) Look for highest energy cluster
    clenergies_ordered = sorted([ (ic , en) for ic, en in enumerate(pfCluster_energy)], 
                                                    key=itemgetter(1), reverse=True)
    if debug: print ("biggest cluster", clenergies_ordered[0])

    # Now iterate over clusters in order of energies
    for iw, (icl, clenergy) in enumerate(clenergies_ordered):
        cl_ieta = pfCluster_ieta[icl]
        cl_iphi = pfCluster_iphi[icl]
        cl_iz = pfCluster_iz[icl]
        cl_eta = pfCluster_eta[icl]
        cl_phi = pfCluster_phi[icl]

        is_in_window = False
        # Check if it is already in one windows
        for window in windows_map.values():
            is_in_window, (ietaw, iphiw) = in_window(*window["seed"], cl_ieta, cl_iphi, cl_iz) 
            if is_in_window:
                nonseed_clusters.append(icl)
                break

        # If is not already in some window 
        if not is_in_window: 
            caloseed = pfcluster_calo_map[icl]
            if caloseed == -1:
                nocalowN+=1
                # Not creating too many windows of noise
                if nocalowN> nocalowNmax: continue
            # Let's create  new window:
            new_window = {
                "seed": (cl_ieta, cl_iphi, cl_iz),
                "calo" : caloseed,
                "metadata": {
                    "seed_eta": cl_eta,
                    "seed_phi": cl_phi, 
                    "seed_iz": cl_iz,
                    "en_seed": pfCluster_energy[icl],
                    "en_true": calo_simenergy[caloseed] if caloseed!=-1 else 0, 
                    "is_calo": caloseed != -1
                }
            }
            
            # Create a unique index
            windex = "".join([ random.choice(string.ascii_lowercase) for _ in range(8)])
            new_window["metadata"]["index"] = windex
            # Save the window
            windows_map[windex] = new_window
            # isin, mask = fill_window_cluster(new_window, clxtals_ieta, clxtals_iphi, clxtals_iz, 
            #                     clxtals_energy, clxtals_rechitEnergy, pfcluster_calo_map[icl], fill_mask=True)
            # Save also seed cluster for cluster_masks
            clusters_event.append({
                    "window_index": new_window["metadata"]["index"],
                    "cluster_deta": 0.,
                    "cluster_dphi": 0., 
                    "cluster_iz" : cl_iz,
                    "en_cluster": pfCluster_energy[icl],
                    "is_seed": True,
                    "in_scluster":  pfcluster_calo_map[icl] == new_window["calo"],
                })

           
    # Now that all the seeds are inside let's add the non seed
    for icl_noseed in nonseed_clusters:
        cl_ieta = pfCluster_ieta[icl_noseed]
        cl_iphi = pfCluster_iphi[icl_noseed]
        cl_iz = pfCluster_iz[icl_noseed]
        cl_eta = pfCluster_eta[icl_noseed]
        cl_phi = pfCluster_phi[icl_noseed]

        # Fill all the windows
        for window in windows_map.values():
            isin, (ietaw, iphiw) = in_window(*window["seed"], cl_ieta, cl_iphi, cl_iz)
            if isin:
                cevent = {
                    "window_index": window["metadata"]["index"],
                    "cluster_dphi": DeltaPhi(cl_phi, window["metadata"]["seed_phi"]), 
                    "cluster_iz" : cl_iz,
                    "en_cluster": pfCluster_energy[icl_noseed],
                    "is_seed": False,
                    "in_scluster":  pfcluster_calo_map[icl_noseed] == window["calo"]
                }
                if window["metadata"]["seed_eta"] > 0:
                    cevent["cluster_deta"] = cl_eta - window["metadata"]["seed_eta"]
                else:
                    cevent["cluster_deta"] = window["metadata"]["seed_eta"] - cl_eta
                
                clusters_event.append(cevent)



    ###############################
    #### Add rechits and
    
    for window in windows_map.values():
        calo_seed = window["calo"]
        # Check the type of events
        # - Number of pfcluster associated, 
        # - deltaR of the farthest cluster
        # - Energy of the pfclusters
        if calo_seed != -1:
            # Get number of associated clusters
            assoc_clusters =  calo_pfcluster_map[calo_seed]
            max_en_pfcluster = max([pfCluster_energy[i] for i in assoc_clusters])
            max_dr = max( [ DeltaR(calo_simphi[calo_seed], calo_simeta[calo_seed], 
                            pfCluster_phi[i], pfCluster_eta[i]) for i in assoc_clusters])
            window["metadata"]["nclusters"] = len(assoc_clusters)
            window["metadata"]["max_en_cluster"] = max_en_pfcluster
            window["metadata"]["max_dr_cluster"] = max_dr

    
    # Save metadata in the cluster items
    for clw in clusters_event:
        clw.update(windows_map[clw["window_index"]]["metadata"])

    clusters_masks += clusters_event
        
# results = np.array(energies_maps)
# meta= pd.DataFrame(metadata)

#results_nocalo = np.array(energies_maps_nocalo)
#np.save("data_calo.npy", results)

#meta.to_csv("metadata_windows.csv", index=False)
#np.save("data_nocalo.npy", results_nocalo)

#pickle.dump(clusters_masks, open("clusters_masks.pkl", "wb"))

df_cl = pd.DataFrame(clusters_masks) 
pickle.dump(df_cl, open(args.outputfile, "wb"))
