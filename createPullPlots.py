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

import ROOT

import os

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist');
fileList = os.listdir(os.getcwd());
fileList.sort();

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist3a');
fileList1 = os.listdir(os.getcwd());
fileList1.sort();

import ROOT
from ROOT import TGraphErrors, TGraph, gPad, TMultiGraph, TFile, TCanvas, TF1,TPaveStats, TLegend, TObject, RooRealVar, RooDataSet, RooArgSet, RooAbsData
import time, sys

#ROOT.SetMemoryPolicy(ROOT.kMemoryHeuristics);

#graphHolder = TMultiGraph()

#print fileList
#sys.exit(0)
#fileList = ["fitresultlist_0000.root"]
#fileList1 = ["fitresultlist1_0000.root"]

dirList = os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist'
dirList1 = os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist3a'
dirDsMean = os.environ['B2DXFITTERSROOT']+'/tutorial/dsMean'

os.chdir(dirDsMean);
listDsMean = os.listdir(os.getcwd());
listDsMean.sort();

if(len(fileList)==0):
    print "No files found in fitresultlist folder"
    sys.exit(1);

if(len(fileList1)==0):
    print "No files found in fitresultlist2 folder"
    sys.exit(1);

if(len(dirDsMean)==0):
    print "No files found in dsMean folder"
    sys.exit(1);
'''
dsMean_file = TFile(dirDsMean+'/'+listDsMean[0]);

dirKeyList= dsMean_file.GetListOfKeys();
for i in range(dirKeyList.GetSize()):
    dirKeyList.At(i).ReadObj().Print();

sys.exit(0);
'''

in_file_a = TFile(dirList1+'/'+fileList1[0]);
keyList_a = in_file_a.GetListOfKeys();

for i in range(keyList_a.GetSize()):
    keyList_a.At(i).ReadObj().Print();

sys.exit(0);

firstFile = -1;
firstFile1 = -1;

fileList.sort();
fileList1.sort();

linFuncList = []

p1Dev = RooRealVar("p1Dev","p1Dev",0);
p1DevSet = RooDataSet("p1DevSet","p1DevSet",RooArgSet(p1Dev));


p0Dev = RooRealVar("p0Dev","p0Dev",0);
p0DevSet = RooDataSet("p0DevSet","p0DevSet",RooArgSet(p0Dev));

for it in fileList[:100]:
    if it[-5:]!='.root':
        continue

    it1 = "fitresultlist2_" + it[-9:]; 
    
    if it1 not in fileList1:
        continue
    
    itDir = "dsMean_" + it[-9:];
    dsMean_file = TFile(dirDsMean+'/'+ itDir);

    in_file1 = TFile(dirList1+"/"+it1)
    in_file = TFile(dirList+"/"+it)
    ROOT.SetOwnership(in_file, False)
    ROOT.SetOwnership(in_file1, False)
    
    if(in_file1.IsZombie() or in_file.IsZombie() or dsMean_file.IsZombie()):
        continue
    
    if firstFile ==-1:
        firstFile = it[-9:-5]

    lastFile = it[-9:-5]
    
    if firstFile1 ==-1:
        firstFile1 = it[-9:-5]

    lastFile1 = it[-9:-5]
    
    #Get objects from firstFile1
    keyList1 = in_file1.GetListOfKeys()

    #print "\n\n\nKEYLIST1 =",keyList1,"\n\n\n\n\n"
    #print keyList1.GetSize()

    for i in range(keyList1.GetSize()):
        keyList1.At(i).ReadObj().Print();

    dirKeyList= dsMean_file.GetListOfKeys();
    for i in range(dirKeyList.GetSize()):
        dirKeyList.At(i).ReadObj().Print();

    dsMeanVal = dirKeyList.At(0).ReadObj();
    '''
    sys.exit(0);
    '''

    #etaAvg = RooRealVar();
    #p0End = TObject();
    #p1End = TObject();

    #in_file1.GetObject('etaMean',etaAvg);
    #in_file1.GetObject('Bs2DsPi_mistagcalib_p0',p0End);
    #in_file1.GetObject('Bs2DsPi_mistagcalib_p1',p1End);
    etaAvg = keyList1.At(0).ReadObj();
    p0End = keyList1.At(2).ReadObj();
    p1End = keyList1.At(1).ReadObj();
    
    print "ETAAVG"
    etaAvg.Print();
    print "P0END"
    p0End.Print();
    print "P1END"
    p1End.Print();

    in_file1.Close();

    #Get objects from firstFile
    
    keyList = in_file.GetListOfKeys()

    #print "\n\n\nKEYLIST =",keyList,"\n\n\n\n\n"
    #print keyList.GetSize()

    for i in range(keyList.GetSize()):
        keyList.At(i).ReadObj().Print();
    '''
    sys.exit(0);
    '''

    #etaAvg = RooRealVar();
    #p0End = TObject();
    #p1End = TObject();
    etaAvgValVarList = keyList.At(0).ReadObj();
    mistagList = keyList.At(1).ReadObj();

    print "ETAAVGVALVARLIST"
    etaAvgValVarList.Print();
    print "MISTAGLIST"
    mistagList.Print();

    in_file.Close();


    #sys.exit(0);

    mistagVsEtaGraph = TGraphErrors(etaAvgValVarList.GetSize())
    
    linFunc = TF1('linFunc','[0]+[1]*x',0.0,0.5);
    #linFunc = TF1('linFunc','[0]+[1]*(x-%f)' % dsMeanVal.getValV(),0.0,0.5);
    ROOT.SetOwnership(linFunc,False);
    linFuncList += [linFunc];
    #linFuncList += [TF1('linFunc','[0]+[1]*x',0.0,0.5)];
    linFuncList[-1].SetParameters(0.0,1.0);
    #ROOT.SetOwnership(linFunc, False)
       
    for i in range(etaAvgValVarList.GetSize()):

        mistagVsEtaGraph.SetPoint(i,etaAvgValVarList.At(i).getValV(),mistagList.At(i).getValV())
        mistagVsEtaGraph.SetPointError(i,etaAvgValVarList.At(i).getError(),mistagList.At(i).getError())
        print etaAvgValVarList.At(i).getError(),mistagList.At(i).getError()
        #mistagVsEtaGraph.SetLineColor(currentColor)
        #linFuncList[-1].SetLineColor(currentColor)
    
    fitresult = mistagVsEtaGraph.Fit(linFuncList[-1],"S","",0.0,0.5)
    
    #print "FITRESULT"
    #fitresult.Print();
    
    p1Fit = fitresult.Parameter(1);
    p1FitError = fitresult.ParError(1);
    print "FITRESULT PARAMETER 0"
    print fitresult.Parameter(0);
    print "FITRESULT PARAMETER 1"
    print fitresult.Parameter(1);
    
    p1End = p1End.getValV();

    p1Dev.setVal((p1Fit - p1End) / p1FitError);
    p1DevSet.add(RooArgSet(p1Dev))

    p0Fit = fitresult.Parameter(0)# - dsMeanVal.getValV();
    p0FitError = fitresult.ParError(0);
    
    p0End = p0End.getValV()-etaAvg.getValV();

    print 'P0FIT = ', p0Fit, '\nDSMEANVAL = ', dsMeanVal.getValV(), '\nP0END = ', p0End, '\n'

    p0Dev.setVal((p0Fit - p0End) / p0FitError);
    p0DevSet.add(RooArgSet(p0Dev))
    #graphHolder.Add(mistagVsEtaGraph)
    #currentColor += 1
    #break;

currentTime = time.time();

theHistCanvas = TCanvas();
p1DevHist = RooAbsData.createHistogram(p1DevSet,"p1Dev",20);
p1DevHist.Fit('gaus');
p1DevHist.Draw();

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists('p1HistPlots')):
    os.mkdir("p1HistPlots")
os.chdir('p1HistPlots');
theHistCanvas.SaveAs("p1Hist_%f.pdf" % currentTime); 

raw_input("Press Enter to continue");

theHistCanvas.Close();

theHistCanvas = TCanvas();
p0DevHist = RooAbsData.createHistogram(p0DevSet,"p0Dev",20);
p0DevHist.Fit('gaus');
p0DevHist.Draw();

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists('p0HistPlots')):
    os.mkdir("p0HistPlots")
os.chdir('p0HistPlots');
theHistCanvas.SaveAs("p0Hist_%f.pdf" % currentTime); 

raw_input("Press Enter to continue");

theHistCanvas.Close();
