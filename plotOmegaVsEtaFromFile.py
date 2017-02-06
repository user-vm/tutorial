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

# figure out which custom allocators are available
# prefer jemalloc over tcmalloc
for i in libjemalloc libtcmalloc; do
    for j in `echo "$LD_LIBRARY_PATH" | tr ':' ' '` \
        /usr/local/lib /usr/lib /lib; do
        for k in `find "$j" -name "$i"'*.so.?' | sort -r`; do
            if test \! -e "$k"; then
            continue
        fi
        echo adding $k to LD_PRELOAD
        if test -z "$LD_PRELOAD"; then
            export LD_PRELOAD="$k"
            break 3
        else
            export LD_PRELOAD="$LD_PRELOAD":"$k"
            break 3
        fi
    done
    done
done

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
'''SEED = None
for tmp in sys.argv[1:]:
    try:
        SEED = int(tmp)
    except ValueError:
        print ('DEBUG: argument %s is no number, trying next argument as'
            'seed') % tmp
if None == SEED:
    print 'ERROR: no seed given'
    sys.exit(1)'''

#SEED = 42

import os

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist');
fileList = os.listdir(os.getcwd());
fileList.sort();

import ROOT
from ROOT import TGraphErrors, TGraph, gPad, TMultiGraph, TFile, TCanvas, TF1
import time, sys

ROOT.SetMemoryPolicy(ROOT.kMemoryHeuristics);

graphHolder = TMultiGraph()

#print fileList
#sys.exit(0)
#fileList = ["fitresultlist_0000.root"]

if(len(fileList)==0):
    print "No .root files found"
    sys.exit(1);

currentColor = 0
#linFuncList = []

firstFile = -1

for it in fileList:
    if it[-5:]!='.root':
        continue
    
    if firstFile ==-1:
        firstFile = it[-9:-5]

    lastFile = it[-9:-5]

    in_file = TFile(it)
    keyList = in_file.GetListOfKeys()

    print "\n\n\n",keyList,"\n\n\n\n\n"
    print keyList.GetSize()

    for i in range(keyList.GetSize()):
        keyList.At(i).ReadObj().Print();

    #sys.exit(0);

    # 0 - etaMean
    # 1 - mistag
    # 2 - ProcessID0

    etaAvgValVarList = keyList.At(1).ReadObj();
    mistagList = keyList.At(0).ReadObj();

    in_file.Close();
    mistagVsEtaGraph = TGraphErrors(etaAvgValVarList.GetSize())

    #linFunc = TF1('linFunc','[0]+[1]*x',0.0,0.5);
    #linFuncList += [linFunc];
    #linFunc.SetParameters(0.0,1.0);
    #ROOT.SetOwnership(linFunc, False)
       
    for i in range(etaAvgValVarList.GetSize()):

        mistagVsEtaGraph.SetPoint(i,etaAvgValVarList.At(i).getValV(),mistagList.At(i).getValV())
        mistagVsEtaGraph.SetPointError(i,etaAvgValVarList.At(i).getError(),mistagList.At(i).getError())
        print etaAvgValVarList.At(i).getError(),mistagList.At(i).getError()
        #mistagVsEtaGraph.SetLineColor(currentColor)
        #linFunc.SetLineColor(currentColor)
        #mistagVsEtaGraph.Fit(linFunc,"","",0.0,0.5)

    graphHolder.Add(mistagVsEtaGraph)
    currentColor += 1
    #break;

os.chdir("..")

theCanvas = TCanvas()
    
if (graphHolder.GetListOfGraphs().GetSize()==1):
    graphHolder.SetTitle("Omega vs. Eta;Eta;Omega")
else:
    graphHolder.SetTitle("Omega vs. Eta (multiple eta sets);Eta;Omega")
    
graphHolder.Draw("ap")

'''
mistagVsEtaGraph.SetTitle("Omega vs. Eta;Eta;Omega");
mistagVsEtaGraph.GetXaxis().SetLimits(0.0,0.5);
mistagVsEtaGraph.GetYaxis().SetRangeUser(0.0,0.5);
mistagVsEtaGraph.Draw("ap");
'''
if lastFile != firstFile:
    theCanvas.Print("omegaVsEtaGraph_%s-%s_%f.pdf" %(firstFile,lastFile,time.time()),"pdf");
else:
    theCanvas.Print("omegaVsEtaGraph_%s_%f.pdf" %(firstFile,time.time()),"pdf");

raw_input("Press Enter to continue");
if(theCanvas!=None):
    theCanvas.Close();

print "SHIT"
