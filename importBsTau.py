#!/bin/sh
# -*- mode: python; coding: utf-8 -*-
# vim: ft=python:sw=4:tw=78:expandtab
# --------------------------------------------------------------------------- 
# @file importBsTau.py
#
# @import BsTau data, plot and determine lifetime
#
# per-event mistag, average sigma_t, spline acceptance
#
# @author Manuel Schiller
# @date 2012-07-08
# --------------------------------------------------------------------------- 
# This file is used as both a shell script and as a Python script.
""":"
# This part is run by the shell. It does some setup which is convenient to save
# work in common use cases.

# make sure the environment is set up properly
if test -n "$CMTCONFIG" \
         -a -f $B2DXFITTERSROOT/$CMTCONFIG/libB2DXFittersDict.so \
     -a -f $B2DXFITTERSROOT/$CMTCONFIG/libB2DXFittersLib.so; then
    # all ok, software environment set up correctly, so don't need to do 
    # anything
    true
else
    if test -n "$CMTCONFIG"; then
    # clean up incomplete LHCb software environment so we can run
    # standalone
        echo Cleaning up incomplete LHCb software environment.
        PYTHONPATH=`echo $PYTHONPATH | tr ':' '\n' | \
            egrep -v "^($User_release_area|$MYSITEROOT/lhcb)" | \
            tr '\n' ':' | sed -e 's/:$//'`
        export PYTHONPATH
        LD_LIBRARY_PATH=`echo $LD_LIBRARY_PATH | tr ':' '\n' | \
            egrep -v "^($User_release_area|$MYSITEROOT/lhcb)" | \
            tr '\n' ':' | sed -e 's/:$//'`
        export LD_LIBRARY_PATH
        exec env -u CMTCONFIG -u B2DXFITTERSROOT "$0" "$@"
    fi
    # automatic set up in standalone build mode
    if test -z "$B2DXFITTERSROOT"; then
        cwd="$(pwd)"
        # try to find from where script is executed, use current directory as
        # fallback
        tmp="$(dirname $0)"
        tmp=${tmp:-"$cwd"}
        # convert to absolute path
        tmp=`readlink -f "$tmp"`
        # move up until standalone/setup.sh found, or root reached
        while test \( \! -d "$tmp"/standalone \) -a -n "$tmp" -a "$tmp"\!="/"; do
            tmp=`dirname "$tmp"`
        done
        if test -d "$tmp"/standalone; then
            cd "$tmp"/standalone
            . ./setup.sh
        else
            echo `basename $0`: Unable to locate standalone/setup.sh
            exit 1
        fi
        cd "$cwd"
        unset tmp
        unset cwd
    fi
fi



# set batch scheduling (if schedtool is available)
schedtool="`which schedtool 2>/dev/zero`"
if test -n "$schedtool" -a -x "$schedtool"; then
    echo "enabling batch scheduling for this job (schedtool -B)"
    schedtool="$schedtool -B -e"
else
    schedtool=""
fi

# set ulimit to protect against bugs which crash the machine: 3G vmem max,
# no more then 8M stack
ulimit -v $((4096 * 1024))
ulimit -s $((   8 * 1024))

# trampoline into python
exec $schedtool /usr/bin/time -v env python -O "$0" - "$@"
"""
__doc__ = """ real docstring """

import sys
SEED = None
for tmp in sys.argv[1:]:
    SEED = str(tmp)

print SEED
SEED = SEED.lower()

if SEED =="ds_tau":
    SEED = "Ds_TAU"
    maxExpFunc = 0.005
elif SEED == "ds_truetau":
    SEED = "Ds_TRUETAU"
    maxExpFunc = 0.005
elif SEED == "bs_truetau":
    maxExpFunc = 0.015
    SEED = "Bs_TRUETAU"
else:
    maxExpFunc = 0.015
    SEED = "Bs_TAU"

print SEED, maxExpFunc

import ROOT
import os, time
from ROOT import TFile,TH1D,TF1,TCanvas

from ROOT import gStyle, TStyle
gStyle.SetOptFit(1111);
gStyle.SetOptStat(111111);

in_file = TFile("/mnt/cdrom/Bs2Dspipipi_MC_fullSel_reweighted_combined.root");
ROOT.SetOwnership(in_file, False)
keyList = in_file.GetListOfKeys()

print "\n\n\n",keyList,"\n\n\n\n\n"
print keyList.GetSize()
'''
for i in range(keyList.GetSize()):
	keyList.At(i).ReadObj().Print();
'''
tree1 = keyList.At(0).ReadObj();
print tree1.GetName();

#tree1.Draw("Ds_TRUEID","",
theCanvas = TCanvas();
bsTauHist = TH1D("%ssTauHist" % SEED[0],"%s Histogram;%s;number" % (SEED,SEED),100,0.0,maxExpFunc);
tree1.Draw("%s>>%ssTauHist" % (SEED,SEED[0]));

histMaxY = bsTauHist.GetMaximum();
histMaxX = bsTauHist.GetBinCenter(bsTauHist.GetMaximumBin());

print "HISTMAXX =", histMaxX, "HISTMAXY =", histMaxY

theCanvas.Close();
theCanvas = TCanvas();
expFunc = TF1("expFunc","%f*exp(-(x-%f)*[0])" % (histMaxY,histMaxX),histMaxX,maxExpFunc);
tree1.Fit("expFunc",SEED,"%s>%f" % (SEED,histMaxX),"","ILL")
#tree1.Draw("SEED,"%s>=0" % SEED,"","ILL");

#tree1.Draw("SEED","%ss_ID>0&&%s>0" % (SEED[0],SEED));

#bsTauHist.Fit("expFunc","IL","",histMaxX+0.00001,maxExpFunc); #<-??? (ILL)
#bsTauHist.Draw();

currentTime = time.time();

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists('BsDsTauPlots')):
    os.mkdir("BsDsTauPlots")
os.chdir('BsDsTauPlots');
theCanvas.SaveAs("%s_Hist_%f.pdf" % (SEED,currentTime));

raw_input("Press Enter to continue");

in_file.Close();

#true Bs lifetime -> 1.47 * 10^-12 s -> 1/lifetime = 6.80 * 10^11
#true Ds lifetime -> 5.0  * 10^-13 s -> 1/lifetime = 2.0  * 10^12
