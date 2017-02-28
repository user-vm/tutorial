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

import ROOT
from ROOT import TFile, RooFit, TTree, RooDataSet, RooArgSet, RooRealVar
import sys,os

def importTupleDict(name):
    
    try:
        lines = file(name, 'r').readlines()
    except:
        print "Reading tuple dictionary from file failed."
        sys.exit(1)
    
    if name != None:
        where = name
    else:
        where = 'unknown location'
    s = ''.join(lines)
    
    d = eval(compile(s, where, 'eval'))
    if dict != type(d):
        raise TypeError('configuration from %s does not evaluate to dictionary' % where)
    
    return d

#tupleDictFilename = "default filename"

tupleDictFilename = str(sys.argv[-1]);

if not os.path.isfile(tupleDictFilename) or tupleDictFilename == "-":
    print "Filename argument invalid; running for default tuple dictionary file"
    tupleDictFilename = os.environ["B2DXFITTERSROOT"] + "/tutorial/tupleDict.py"

in_file = TFile("/mnt/cdrom/Bs2Dspipipi_MC_fullSel_reweighted_combined.root");
ROOT.SetOwnership(in_file, False)
keyList = in_file.GetListOfKeys()

tree1 = keyList.At(0).ReadObj();
print tree1.GetName();

tupleDict = importTupleDict(tupleDictFilename);

print tupleDict.keys()
#sys.exit(0);

varList = []
varRenamedList = []

for i in range(len(tupleDict)):
    varName = tupleDict.keys()[i]
    varList += [RooRealVar(varName,tree1.GetBranch(varName).GetTitle(),tree1.GetMinimum(varName),tree1.GetMaximum(varName))];
    varRenamedList += [RooFit.RenameVariable(varName, tupleDict[varName])]
    #RooFit.RenameVariable(varName, tupleDict[varName]);
    #varList[i].SetName(tupleDict.keys()[i]);
'''
for i in range(len(tupleDict)):
    varList[i].Print()
'''

#def test(a,b,c,d):
#    print "Yes"

#test(*(tupleDict.keys()))

tupleDataSet = RooDataSet("treeData","treeData",tree1,RooArgSet(*varList));

tupleDataSet.get().find(varName).Print();

for i in range(len(tupleDict)):
    varName = tupleDict.keys()[i];
    a = tupleDataSet.get().find(varName);
    a.SetName(tupleDict[varName]);
    a.SetTitle(tupleDict[varName]);

tupleDataSet.Print();

aFrame = tupleDataSet.get().find("fake Bs").frame();
tupleDataSet.get().find("fake Bs").Print();
tupleDataSet.plotOn(aFrame);

doubleCanvas = TCanvas();

aFrame.Draw()

raw_input("Press Enter to continue...")

#vim: sw=4:et
