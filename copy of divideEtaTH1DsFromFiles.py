#!/bin/sh
# -*- mode: python; coding: utf-8 -*-
# vim: ft=python:sw=4:tw=78:expandtab
# --------------------------------------------------------------------------- 
# @file divideEtaTH1DFromFiles.py
#
# @brief Python script to do eta histogram things
#
# @author Manuel Schiller
# @date 2012-02-15 ... ongoing
#
# handles switch between LHCb and standalone environment; loads
# jemalloc/tcmalloc for faster memory allocations in RooFit, enables
# batch scheduling in the OS (if available) for fewer cache misses due to
# longer time slices, and sets a ulimit (so runaway processes cannot crash
# machine, but die)
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
ulimit -v $((3072 * 1024))
ulimit -s $((   8 * 1024))

# trampoline into python
exec $schedtool /usr/bin/time -v env python -O "$0" - "$@"
"""
__doc__ = """ real docstring """

# user code starts here

from ROOT import cout, TFile, RooAbsData, RooDataSet, RooPrintable, RooThresholdCategory, THStack, TF1, RooArgList, TH1D, TH1, TH1F, RooRealVar
from ROOT.Math import GaussIntegrator
import ROOT

def fline(x, par):
   if (x[0] > 2.5 and x[0] < 3.5):
      TF1.RejectPoint();
      return 0;

   return par[0] + par[1]*x[0];

def divideEtaTH1Ds(etaHist,x,numCat,fileNumber,categoryList = None,drawHist=False):

    if categoryList==None:
        categoryList = []
        for i in range(numCat):
            categoryList += ["Cat"+str(i)]

    histSum = etaHist.Integral();
    #print "HISTSUM",histSum, etaHist.Integral(0,50)+etaHist.Integral(51,100),etaHist.Integral(0,50),etaHist.Integral(51,100),"\n";

    limList = [-1];

    for i in range(1,numCat):
        start = limList[i-1]+1;
        targetVal = histSum/numCat;
        left = start;
        right = etaHist.GetNbinsX();
        #print "\n\n\n",etaHist.Integral(start,start+1),"\n\n\n\n";
        while abs(left-right)>1:
            if etaHist.Integral(start,int((left+right)/2))>targetVal:
                right = (left + right) / 2;
            else:
                left = (left + right) / 2;
            #print start, left, right, etaHist.Integral(start,int((left+right)/2)),targetVal,",",

        if abs(etaHist.Integral(start,left)-targetVal) > abs(etaHist.Integral(start,right)-targetVal):
            limList += [right];
        else:
            limList += [left];

    limList[0] = 0;

    print limList
    
    xRegions = RooThresholdCategory("tageffRegion", "region of tageff", x, "Cat"+str(numCat));
    xRegions.writeToStream(cout,False);
    xRegions.writeToStream(cout,True);

    fitResultList = []
    
    #create thresholds and list of fitting functions (all linear, but with
    #different ranges corresponding to the categories
    for i in range(1,numCat):
        xRegions.addThreshold(etaHist.GetXaxis().GetBinCenter(limList[i]),categoryList[i-1]);
        currentRangeTF1 = TF1("fitFuncEtaset"+str(fileNumber)+"Cat"+str(i-1),"[0]+[1]*x",etaHist.GetXaxis().GetBinCenter(limList[i-1]),etaHist.GetXaxis().GetBinCenter(limList[i]));
        fitResultList += [etaHist.Fit(currentRangeTF1,"R0S").Get()];
        currentRangeTF1.IsA().Destructor(currentRangeTF1);
        print "P0, P1 = ",fitResultList[-1].Parameter(0), fitResultList[-1].Parameter(1);
        #raw_input("Press Enter to continue");

    print "\n\n\n\n",drawHist,"\n\n\n\n"
    if drawHist == True:

        #etaSet = RooDataSet('etaSet','etaSet',ds,RooArgSet(ds.get().find['eta']));
        #etaSet.Print();
        #etaHist.SetAxisRange(0.1,0.2);
        #etaHist.SetAxisRange(0.1,0.3);
        ROOT.gStyle.SetPalette(ROOT.kOcean);
    
        #create stack to contain the chopped TH1Ds
        etaHistStack = THStack("etaHistStack", "Stack of TH1Ds");

        limList += [etaHist.GetNbinsX()];
        histCutterFunc = TF1("histCutterFunc","((x>=[0])?((x<[1])?1:0):0)*x",0.0,1.0);

        for i in range(len(limList)-1):
        
            etaHistClone = etaHist.Clone();
            #etaHistClone.SetBins(limList[i+1]-limList[i],etaHist.GetBinContent(limList[i]),etaHist.GetBinContent(limList[i+1]));
            histCutterFunc.SetParameter(0,etaHist.GetXaxis().GetBinCenter(limList[i]));
            histCutterFunc.SetParameter(1,etaHist.GetXaxis().GetBinCenter(limList[i+1]));
            etaHistClone.Multiply(histCutterFunc);
            etaHistClone.SetFillColor(38+i);
            #etaHist.DrawCopy("hist PFC");
            etaHistStack.Add(etaHistClone);
    
        etaHistStack.Draw("hist PFC");
        #s = raw_input("Press Enter to continue...");

    return xRegions,x

import os

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/etaHist');
fileList = os.listdir(os.getcwd());

#xList = RooArgList
xRegionsList = RooArgList('Threshold list');
fNum = 0;

#parse etaHist directory for .root files
for i in fileList[:1]:
    if(i[-5:]!='.root'):
        continue
    print i
    inFile = TFile(i);
    inFile.GetListOfKeys().Print();
    inFile.ls();
    #s = raw_input("Press Enter to continue");
    theTH1DHist = TH1F();
    inFile.GetObject("etaHist",theTH1DHist);
    #rooRealVarList += [RooRealVar('x','x',0.0,1.0)];
    x = RooRealVar('x','x',0.0,1.0);
    xRegions,x = divideEtaTH1Ds(theTH1DHist,x,5,fNum);
    fNum+=1;
    #xList += [RooAbsReal(x)]
    xRegionsList.add(xRegions.clone(xRegions.GetName()+"_clone"));
    #etasetDataset.add();

import sys
#sys.exit(0);

for i in range(xRegionsList.getSize()):
    xRegionsList.at(0).Print();#.Print();#writeToStream(ROOT.cout,True);

print "\n\nNOCRASH2\n\n"

from ROOT import TFile
import time

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');

f = TFile('xRegionsList_%f.root' % time.time(), 'recreate')
f.WriteTObject(xRegionsList, 'xRegionsList_%f' % time.time())
f.Close()
del f
