#!/bin/sh
# -*- mode: python; coding: utf-8 -*-
# vim: ft=python:sw=4:tw=78:expandtab
# --------------------------------------------------------------------------- 
# @file plotOmegaVsEtaFromFile.py
#
# @brief hands-on session example 3 (B2DXFitters workshop, Padova, 2015)
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
# -----------------------------------------------------------------------------
# Load necessary libraries
# -----------------------------------------------------------------------------


# start by getting seed number
import sys
SEED = None
for tmp in sys.argv[1:]:
    SEED = str(tmp)

print SEED

if SEED !="a" and SEED != "b":
    SEED = ""

import os

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist123%s' % SEED);
fileList = os.listdir(os.getcwd());
fileList.sort();

import ROOT
from ROOT import TGraphErrors, TGraph, gPad, TMultiGraph, TFile, TCanvas, TF1,TPaveStats, TLegend, TObject, RooDataSet, RooRealVar, RooArgSet, RooAbsData
import time, sys

#ROOT.SetMemoryPolicy(ROOT.kMemoryHeuristics);

graphHolder = TMultiGraph()

#print fileList
#sys.exit(0)
#fileList = ["fitresultlist123_0000.root"]

if(len(fileList)==0):
    print "No .root files found"
    sys.exit(1);

currentColor = 0
linFuncList = []
ROOT.SetOwnership(graphHolder,False);

firstFile = -1

p1Dev = RooRealVar("p1Dev","p1Dev",0);
p1DevSet = RooDataSet("p1DevSet","p1DevSet",RooArgSet(p1Dev));


p0Dev = RooRealVar("p0Dev","p0Dev",0);
p0DevSet = RooDataSet("p0DevSet","p0DevSet",RooArgSet(p0Dev));

p0End = 0.350 - (0.05 if SEED=="a" else 0.0)
p1End = 1.000 + (0.05 if SEED=="b" else 0.0)

for it in fileList:
    if it[-5:]!='.root':
        continue
    
    if firstFile ==-1:
        firstFile = it[-9:-5]

    lastFile = it[-9:-5]

    in_file = TFile(it)
    ROOT.SetOwnership(in_file, False)
    keyList = in_file.GetListOfKeys()

    print "\n\n\n",keyList,"\n\n\n\n\n"
    print keyList.GetSize()

    for i in range(keyList.GetSize()):
        keyList.At(i).ReadObj().Print();
    
    #sys.exit(0);

    # 0 - etaAvgList (per-category avg. etas)
    # 1 - etaAvg (avg. eta for all events)
    # 2 - genEtaList (mistagList?)
    # 3 - ProcessID0

    etaAvgValVarList = keyList.At(0).ReadObj();
    etaAvg = keyList.At(1).ReadObj();
    mistagList = keyList.At(2).ReadObj();

    in_file.Close();
    mistagVsEtaGraph = TGraphErrors(etaAvgValVarList.GetSize())

    linFunc = TF1('linFunc','[0]+[1]*(x-%f)' % etaAvg.getValV(),0.0,0.5);
    ROOT.SetOwnership(linFunc,False);
    linFuncList += [linFunc];
    #linFuncList += [TF1('linFunc','[0]+[1]*x',0.0,0.5)];
    linFuncList[-1].SetParameters(etaAvg.getValV(),1.0);
    #ROOT.SetOwnership(linFunc, False)
       
    for i in range(etaAvgValVarList.GetSize()):

        mistagVsEtaGraph.SetPoint(i,etaAvgValVarList.At(i).getValV(),mistagList.At(i).getValV())
        mistagVsEtaGraph.SetPointError(i,etaAvgValVarList.At(i).getError(),mistagList.At(i).getError())
        print etaAvgValVarList.At(i).getError(),mistagList.At(i).getError()
        #mistagVsEtaGraph.SetLineColor(currentColor)
        #linFuncList[-1].SetLineColor(currentColor)
    
    fitresult = mistagVsEtaGraph.Fit(linFuncList[-1],"FQS","",0.0,0.5)
        
    p1Fit = fitresult.Parameter(1);
    p1FitError = fitresult.ParError(1);
    print "FITRESULT PARAMETER 0"
    print fitresult.Parameter(0);
    print "FITRESULT PARAMETER 1"
    print fitresult.Parameter(1);

    p1Dev.setVal((p1Fit - p1End) / p1FitError);
    p1DevSet.add(RooArgSet(p1Dev))

    p0Fit = fitresult.Parameter(0)# - dsMeanVal.getValV();
    p0FitError = fitresult.ParError(0);

    print 'P0FIT = ', p0Fit, '\nDSMEANVAL = ', etaAvg.getValV(), '\nP0END = ', p0End, '\n'

    p0Dev.setVal((p0Fit - p0End) / p0FitError);
    p0DevSet.add(RooArgSet(p0Dev))
    #break;

currentTime = time.time();

theHistCanvas = TCanvas();
p1DevHist = RooAbsData.createHistogram(p1DevSet,"p1Dev",20);
p1DevHist.Fit('gaus');
p1DevHist.Draw('B');

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists('p1HistPlots')):
    os.mkdir("p1HistPlots")
os.chdir('p1HistPlots');
theHistCanvas.SaveAs("p1Hist_p0=%.3f_p1=%.3f_%f.pdf" % (p0End, p1End, currentTime)); 

raw_input("Press Enter to continue");

theHistCanvas.Close();

theHistCanvas = TCanvas();
p0DevHist = RooAbsData.createHistogram(p0DevSet,"p0Dev",20);
p0DevHist.Fit('gaus');
p0DevHist.Draw('B');

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists('p0HistPlots')):
    os.mkdir("p0HistPlots")
os.chdir('p0HistPlots');
theHistCanvas.SaveAs("p0Hist_p0=%.3f_p1=%.3f_%f.pdf" % (p0End, p1End, currentTime));

raw_input("Press Enter to continue");

theHistCanvas.Close();
#vim: sw=4:et
