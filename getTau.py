#!/bin/sh
# -*- mode: python; coding: utf-8 -*-
# vim: ft=python:sw=4:tw=78:expandtab
# --------------------------------------------------------------------------- 
# @file prolog.py
#
# @brief Python script prolog to set up environment correctly
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

import ROOT
from ROOT import TFile, RooRealVar, RooDataSet, RooArgSet, RooFit

import sys

originSuffix = ''

for SEED in sys.argv:
    if SEED.upper() == 'DATA' or SEED.upper() == 'MC':
        originSuffix = SEED.upper();
        break;

if originSuffix == '':
    originSuffix = 'MC'

if originSuffix == 'MC':
    in_file = TFile('/mnt/cdrom/Bs2Dspipipi_MC_fullSel_reweighted_combined.root', 'READ')
else:
    in_file = TFile('/mnt/cdrom/data_Bs2Dspipipi_11_final_sweight.root', 'READ')

ROOT.SetOwnership(in_file, False)
keyList = in_file.GetListOfKeys()
keyList.Print();

keyList.At(0).Print();

tree1 = keyList.At(0).ReadObj();

varList = []
varNames = ['Bs_TRUETAU','Bs_ct']

maxV = 0.0;

for varName in varNames:
    varList += [RooRealVar(varName,tree1.GetBranch(varName).GetTitle(),tree1.GetMinimum(varName),tree1.GetMaximum(varName))];
    maxV = max(maxV,tree1.GetMaximum(varName));

## variables
if originSuffix == 'MC':
    weight = RooRealVar('weight', 'weight', -1e7, 1e7) # MC
    varName = 'weight'
else:
    weight = RooRealVar('N_Bs_sw', 'weight', -1e7, 1e7) # data
    varName = 'N_Bs_sw'

weightVarName = varName

varList += [RooRealVar(varName,tree1.GetBranch(varName).GetTitle(),tree1.GetMinimum(varName),tree1.GetMaximum(varName))];

tupleDataSet = RooDataSet("tupleDataSet", "tupleDataSet",
    RooArgSet(*varList),
    RooFit.Import(tree1))

tupleDataSet.Print();

tmt = RooRealVar('tMinusT','tMinusT',0,-maxV,maxV);

#tDataSet = RooDataSet('tDataSet','tDataSet',RooArgSet(tmt,weightvar), RooFit.WeightVar(weightvar));

from ROOT import TH1D

tHist = TH1D('tDataSet','tDataSet',100,-0.3,0.3)#RooArgSet(tmt,weightvar), RooFit.WeightVar(weightvar));

for i in range(tupleDataSet.numEntries()):
    
    tmt.setVal(tupleDataSet.get(i).find('Bs_ct').getValV()-tupleDataSet.get(i).find('Bs_TRUETAU').getValV()*1000.0);
    #tDataSet.add(RooArgSet(tmt,weightvar),tupleDataSet.get(i).find(weightVarName).getValV());
    tHist.Fill(tmt.getValV(),tupleDataSet.get(i).find(weightVarName).getValV());
    #print tupleDataSet.get(i).find(weightVarName).getValV(),"   ",tDataSet.weight()

#tupleDataSet.merge(tDataSet);

tHist.Fit('gaus');

from ROOT import TCanvas
aCanvas = TCanvas();
'''
tDataSet.Print();

tDataSet = tDataSet.reduce("tMinusT<1&&tMinusT>-1");

tmt = tDataSet.get().find('tMinusT');
tmt.setMax(0.3);
tmt.setMin(-0.3);

aFrame = tmt.frame()

tDataSet.plotOn(aFrame);'''

tHist.setTitle(
tHist.Draw();

aCanvas.SaveAs('a_plot_t_%s.pdf' % originSuffix)

raw_input('Press Enter to continue');

import sys

sys.exit(0);

#in_file.Close();
#tree1.Print();

#print keyList.fSize;

for i in range(keyList.GetEntries()):
    print i," ---> ",
    keyList.At(i).Print();

#print tree1.GetName();

objList = tree1.GetListOfBranches().Clone();

for i in range(objList.GetEntries()):
    print objList.At(i).GetName();

in_file.Close();

#vim: sw=4:et