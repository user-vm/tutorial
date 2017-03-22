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

import os,sys

originSuffix = ''

for SEED in sys.argv:
    if SEED.upper() == 'DATA' or SEED.upper() == 'MC':
        originSuffix = SEED.upper();
        break;

if originSuffix == '':
    originSuffix = 'MC'

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/fitresultlist%s' % originSuffix);
fileList = os.listdir(os.getcwd());
fileList.sort();

numFiles = len(fileList)
i=0

while i<numFiles:
    if '_' not in fileList[i] or fileList[i][-6:]=='1.root':
        fileList.pop(i)
        numFiles-=1
    else:
        i+=1

import ROOT
from ROOT import TGraphErrors, TGraph, gPad, TMultiGraph, TFile, TCanvas, TF1,TPaveStats, TLegend, TObject 
import time, sys

#ROOT.SetMemoryPolicy(ROOT.kMemoryHeuristics);

graphHolder = TMultiGraph()

#print fileList
#sys.exit(0)
#fileList = ["fitresultlist123a_0000.root"]

if(len(fileList)==0):
    print "No .root files found"
    sys.exit(1);

currentColor = 2
linFuncList = []
ROOT.SetOwnership(graphHolder,False);

firstFile = -1

sumP0 = 0.0;
sumP1 = 0.0;
sumAvgEta = 0.0;
numP = 0;

from ROOT import RooRealVar, RooDataSet, RooArgSet

p0Var = RooRealVar('p0Var','p0Var',0.5,-1.0,1.0);
p1Var = RooRealVar('p1Var','p1Var',1.0,0.0,1.5);
pDataSet = RooDataSet('pDataSet','pDataSet',RooArgSet(p0Var,p1Var));

for it in fileList[-1:]:
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
    
    #sys.exit(0);

    # 0 - etaAvgList (per-category avg. etas)
    # 1 - etaAvg (avg. eta for all events)
    # 2 - genEtaList (mistagList?)
    # 3 - ProcessID0

    etaAvgValVarList = keyList.At(0).ReadObj();
    etaAvg = keyList.At(1).ReadObj();
    mistagList = keyList.At(2).ReadObj();

    etaAvgValVarList.Print()
    etaAvg.Print()
    mistagList.Print()

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
        linFuncList[-1].SetLineColor(currentColor)
    
    fitresult = mistagVsEtaGraph.Fit(linFuncList[-1],"FQS","",0.0,0.5)
    p0 = fitresult.Parameter(0);
    p1 = fitresult.Parameter(1);
    p0Error = fitresult.ParError(0);
    p1Error = fitresult.ParError(1);
    
    p0Var.setVal(p0);
    p0Var.setError(p0Error);
    p1Var.setVal(p1);
    p1Var.setError(p1Error);

    pDataSet.add(RooArgSet(p0Var,p1Var));

    sumP0 += float(p0);
    sumP1 += float(p1);
    sumAvgEta += etaAvg.getValV()
    numP += 1;

    graphHolder.Add(mistagVsEtaGraph)
    currentColor = currentColor%9 + 1
    #break;

os.chdir("..")

theCanvas = TCanvas()
    
if (graphHolder.GetListOfGraphs().GetSize()==1):
    graphHolder.SetTitle("#omega vs. #eta_{i};#eta_{i};#omega(#eta_{i})")
else:
    graphHolder.SetTitle("#omega vs. #eta_{i} (%d data sets);#eta_{i};#omega(#eta_{i})" % numP)

graphHolder.Draw("ap");
graphHolder.GetXaxis().SetLimits(0.0,0.5);
graphHolder.SetMinimum(0.0);
graphHolder.SetMaximum(0.5);    
#graphHolder.Draw("ap")

graphHolder.GetYaxis().SetTitleSize(0.05);
graphHolder.GetXaxis().SetTitleSize(0.05);

leg = TLegend(0.1,0.7,0.4,0.9);#,"a fucking header","tlNDC");
ROOT.SetOwnership(leg,False);
#leg.AddEntry(TObject(),"crap");

leg.AddEntry(mistagVsEtaGraph,"data points","lep");
leg.AddEntry(linFuncList[-1],"linear fit","l");
leg.AddEntry(None,"#bar{p_{0}} = %.4f" % (sumP0/numP),"");
leg.AddEntry(None,"#bar{p_{1}} = %.4f" % (sumP1/numP),"");
leg.AddEntry(None,"#LT#eta#GT = %.4f" % (sumAvgEta/numP),"");

leg.Draw();

pDataSet.meanVar(pDataSet.get().find('p0Var')).Print();
pDataSet.meanVar(pDataSet.get().find('p1Var')).Print();

'''
theCanvas.Update()
st = mistagVsEtaGraph.GetListOfFunctions().FindObject("stats")
print st
st.SetX1NDC(0.0);
st.SetX2NDC(1.0);
st,SetY1NDC(0.0);
st.SetY2NDC(1.0);
theCanvas.Modified()
'''
'''
st = TPaveStats(0.0,0.0,0.0,0.0);
st.AddLine(0.0,0.0,0.0,0.0);
'''

#theCanvas.BuildLegend()

'''
mistagVsEtaGraph.SetTitle("Omega vs. Eta;Eta;Omega");
mistagVsEtaGraph.GetXaxis().SetLimits(0.0,0.5);
mistagVsEtaGraph.GetYaxis().SetRangeUser(0.0,0.5);
mistagVsEtaGraph.Draw("ap");
'''

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists('OmegaVsEtaGraphs')):
    os.mkdir("OmegaVsEtaGraphs")
os.chdir('OmegaVsEtaGraphs');

if lastFile != firstFile:
    theCanvas.Print("omegaVsEtaGraph_%s-%s_%f.pdf" %(firstFile,lastFile,time.time()),"pdf");
else:
    theCanvas.Print("omegaVsEtaGraph_%s_%f.pdf" %(firstFile,time.time()),"pdf");

raw_input("Press Enter to continue");
if(theCanvas!=None):
    theCanvas.Close();

ROOT.SetOwnership(theCanvas, False);

print "SHIT"
