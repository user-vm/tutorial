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

from ROOT import cout, TFile, RooAbsData, RooDataSet, RooPrintable, RooThresholdCategory, THStack, TF1, RooArgList, TH1D, TH1, TH1F, RooRealVar, TList, TObjString, TCanvas, TFitResult, TObject
from ROOT.Math import GaussIntegrator
import ROOT

def divideEtaTH1Ds(etaHist,numCat,sourceFileName = None,categoryList = None,drawHist=False):
    # etaHist - the TH1D to split into categories
    # numCat - number of tagging categories
    # categoryList - list of tagging category names
    # drawHist - whether or not to display each category-split histogram
    # sourceFileName - name of etaHist root file

    #normalize etaHist
    etaHist.Scale(1.0/etaHist.Integral());

    #create default category names if none are given
    if categoryList==None:
        categoryList = []
        for i in range(numCat):
            categoryList += ["Cat"+str(i)]

    histSum = etaHist.Integral();
    
    #get list of limits
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
    limList+= [etaHist.GetNbinsX()];

    print limList

    #rangeFit is a 4-element TList containing:
    # - the sourceFileName as element 0
    # - a RooThresholdCategory as element 2, and its RooRealVar as element 1
    # - a tList of tFitResult as element 3
    rangeFit = TList();
    rangeFit.AddLast(TObjString(sourceFileName));
    rangeFit.AddLast(RooRealVar('x','x',0.0,1.0));
    rangeFit.AddLast(RooThresholdCategory("tageffRegion", "region of tageff", rangeFit.At(1), "Cat"+str(numCat)));
    rangeFit.AddLast(TList());

    #plot each category-split histogram, if necessary
    if drawHist == True:

        ROOT.gStyle.SetPalette(ROOT.kOcean);
    
        #create stack to contain the category TH1Ds
        etaHistStack = THStack("etaHistStack", "Stack of TH1Ds");

        #create category-masking function for TH1D clones
        histCutterFunc = TF1("histCutterFunc","((x>=[0])?((x<[1])?1.0:0.0):0.0)",0.0,1.0);

        for i in range(len(limList)-1):
        
            etaHistClone = etaHist.Clone();
            histCutterFunc.SetParameter(0,etaHist.GetXaxis().GetBinCenter(limList[i]));
            histCutterFunc.SetParameter(1,etaHist.GetXaxis().GetBinCenter(limList[i+1]));
            #histCutterFunc.Draw();
            #raw_input("Press Enter to continue to next hisCutterFunc");
            etaHistClone.Multiply(histCutterFunc);
            etaHistClone.SetFillColor(38+i);
            etaHistStack.Add(etaHistClone);

        etaHistClone = etaHist.Clone();
        etaHistClone.SetFillColor(38+len(limList));
        #etaHistStack.Add(etaHistClone);
        
        import time

        os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');

        if(not(os.path.isdir('fits'))):
            os.mkdir('fits');

        os.chdir('fits');
        histCanvas = TCanvas();
        etaHistStack.Draw("hist PFC");
        #etaHistClone.Draw("hist PFC");
        #histCanvas.SaveAs('tagRegionFitList_%f.pdf' % time.time());
    
    #create thresholds and fitting functions (all linear, but with different ranges corresponding to the categories)

    currentRangeTF1List = TList();
    
    for i in range(1,numCat+1):
        if(i<=numCat):
            rangeFit.At(2).addThreshold(etaHist.GetXaxis().GetBinCenter(limList[i]),categoryList[i-1]);
        currentRangeTF1List.AddLast(TF1("fitFuncEtaset","[0]+[1]*(x-"+str(etaHist.Integral(limList[i-1],limList[i])/(limList[i]-limList[i-1]))+")",etaHist.GetXaxis().GetBinCenter(limList[i-1]),etaHist.GetXaxis().GetBinCenter(limList[i])));
        #currentRangeTF1 = TF1("fitFuncEtaset","[0]+[1]*x",etaHist.GetXaxis().GetBinCenter(limList[i-1]),etaHist.GetXaxis().GetBinCenter(limList[i]));
        rangeFit.Last().AddLast(etaHist.Fit(currentRangeTF1List.Last(),"R0S").Get().Clone());
        if (drawHist==True):
            currentRangeTF1List.Last().DrawCopy('same');
        #raw_input('Press Enter to continue to next fit function');
        #currentRangeTF1.IsA().Destructor(currentRangeTF1);
        #print "P0, P1 = ",rangeFit.Last().Last().Parameter(0), rangeFit.Last().Last().Parameter(1);
    
    histCanvas.SaveAs('tagRegionFitList_%f.pdf' % time.time());
    currentRangeTF1List.Delete();
    #for i in range(1,numCat+1):
        #currentRangeTF1List.Last().IsA().Destructor(currentRangeTF1List.Last());
    
    #s = raw_input("Press Enter to continue...");

    return rangeFit

import os

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial/etaHist');
fileList = os.listdir(os.getcwd());

#TList containing relevant data for each eta set in directory
mainResultList = TList();

#number of tagging categories
numTagCat = 5;

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
    mainResultList.AddLast(divideEtaTH1Ds(theTH1DHist,numTagCat,i,None,True));
    

from ROOT import TFile
import time

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');

if(not(os.path.isdir('fits'))):
    os.mkdir('fits');

os.chdir('fits');

mainResultList.Print("",5);

f = TFile('tagRegionFitList_%f.root' % time.time(), 'recreate')
f.WriteTObject(mainResultList, 'tagRegionFitList_%f' % time.time())
f.Close()
del f
