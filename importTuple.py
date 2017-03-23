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
from ROOT import TFile, RooFit, TTree, RooDataSet, RooArgSet, RooRealVar, TCanvas
import sys,os,time
'''
def buildTimePdf(config):
    """
    build time pdf, return pdf and associated data in dictionary
    """
    from B2DXFitters.WS import WS
    print 'CONFIGURATION'
    for k in sorted(config.keys()):
        print '    %32s: %32s' % (k, config[k])
    
    # start building the fit
    ws = RooWorkspace('ws_%s' % config['Context'])
    one = WS(ws, RooConstVar('one', '1', 1.0))
    zero = WS(ws, RooConstVar('zero', '0', 0.0))
    
    # start by defining observables
    time = WS(ws, RooRealVar('time', 'time [ps]', 0.2, 15.0))
    qf = WS(ws, RooCategory('qf', 'final state charge'))
    qf.defineType('h+', +1)
    qf.defineType('h-', -1)
    qt = WS(ws, RooCategory('qt', 'tagging decision'))
    qt.defineType(      'B+', +1)
    qt.defineType('Untagged',  0)
    qt.defineType(      'B-', -1)
    
    # now other settings
    Gamma  = WS(ws, RooRealVar( 'Gamma',  'Gamma',  0.661)) # ps^-1
    DGamma = WS(ws, RooRealVar('DGamma', 'DGamma',  0.106)) # ps^-1
    Dm     = WS(ws, RooRealVar(    'Dm',     'Dm', 17.719)) # ps^-1
    
    # HACK (1/2): be careful about lower bound on eta, since mistagpdf below
    # is zero below a certain value - generation in accept/reject would get
    # stuck
    if 'GEN' in config['Context'] or 'FIT' in config['Context']:
        eta = WS(ws, RooRealVar('eta', 'eta', 0.35,
                 0.0 if 'FIT' in config['Context'] else (1. + 1e-5) * max(0.0,
                 config['TrivialMistagParams']['omega0']), 0.5))

    mistag = WS(ws, RooRealVar('mistag', 'mistag', 0.35, 0.0, 0.5))
    tageff = WS(ws, RooRealVar('tageff', 'tageff', 1.0))
    timeerr = WS(ws, RooRealVar('timeerr', 'timeerr', 0.040, 0.001, 0.100))
    # fit average mistag
    # add mistagged 
    #ge rid of untagged events by putting restriction on qf or something when reduceing ds
    # now build the PDF
    from B2DXFitters.timepdfutils import buildBDecayTimePdf
    from B2DXFitters.resmodelutils import getResolutionModel
    from B2DXFitters.acceptanceutils import buildSplineAcceptance
    
    if 'GEN' in config['Context']:
        obs = [ qf, qt, time, eta]
    else:
        obs = [ qf, qt, time]
    acc, accnorm = buildSplineAcceptance(ws, time, 'Bs2DsPi_accpetance',
            config['SplineAcceptance']['KnotPositions'],
            config['SplineAcceptance']['KnotCoefficients'][config['Context'][0:3]],
            'FIT' in config['Context']) # float for fitting
    if 'GEN' in config['Context']:
        acc = accnorm # use normalised acceptance for generation
    # get resolution model
    resmodel, acc = getResolutionModel(ws, config, time, timeerr, acc)
    if 'GEN' in config['Context']:
        # build a (mock) mistag distribution
        mistagpdfparams = {} # start with parameters of mock distribution
        for sfx in ('omega0', 'omegaavg', 'f'):
            mistagpdfparams[sfx] = WS(ws, RooRealVar(
                    'Bs2DsPi_mistagpdf_%s' % sfx, 'Bs2DsPi_mistagpdf_%s' % sfx,
                    config['TrivialMistagParams'][sfx]))
        # build mistag pdf itself
        mistagpdf = WS(ws, MistagDistribution(
                'Bs2DsPi_mistagpdf', 'Bs2DsPi_mistagpdf',
                eta, mistagpdfparams['omega0'], mistagpdfparams['omegaavg'],
                mistagpdfparams['f']))
        mistagcalibparams = {} # start with parameters of calibration
        for sfx in ('p0', 'p1', 'etaavg'):
            mistagcalibparams[sfx] = WS(ws, RooRealVar('Bs2DsPi_mistagcalib_%s' % sfx, 'Bs2DsPi_mistagpdf_%s' % sfx,config['MistagCalibParams'][sfx]));
        
        
        for sfx in ('p0', 'p1'): # float calibration paramters
            mistagcalibparams[sfx].setConstant(False)
            mistagcalibparams[sfx].setError(0.1)
        
        # build mistag pdf itself
        omega = WS(ws, MistagCalibration(
            'Bs2DsPi_mistagcalib', 'Bs2DsPi_mistagcalib',
            eta, mistagcalibparams['p0'], mistagcalibparams['p1'],
            mistagcalibparams['etaavg']))

    # build the time pdf
    if 'GEN' in config['Context']:
        pdf = buildBDecayTimePdf(
            config, 'Bs2DsPi', ws,
            time, timeerr, qt, qf, [ [ omega ] ], [ tageff ],
            Gamma, DGamma, Dm,
            C = one, D = zero, Dbar = zero, S = zero, Sbar = zero,
            timeresmodel = resmodel, acceptance = acc, timeerrpdf = None,
            mistagpdf = [mistagpdf], mistagobs = eta)
    else:
        pdf = buildBDecayTimePdf(
            config, 'Bs2DsPi', ws,
            time, timeerr, qt, qf, [ [ eta ] ], [ tageff ],
            Gamma, DGamma, Dm,
            C = one, D = zero, Dbar = zero, S = zero, Sbar = zero,
            timeresmodel = resmodel, acceptance = acc, timeerrpdf = None)

    return { # return things
            'ws': ws,
            'pdf': pdf,
            'obs': obs
            }
'''
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

tupleDataSet.get().find("SSKaon").SetMaximum(2);
tupleDataSet.get().find("SSKaon").SetMinimum(-2);

aFrame = tupleDataSet.get().find("SSKaon").frame();
tupleDataSet.get().find("SSKaon").Print();
tupleDataSet.plotOn(aFrame);

aFrame.Draw()
raw_input("Press Enter to continue");
'''
tupleDataSet = tupleDataSet.reduce("fake_Bs>=0&&true_Bs>=0");

tupleDataSet.get().find("fake_Bs").setMin(0.0);

tupleDataSet.Print();

aFrame = tupleDataSet.get().find("fake_Bs").frame();
tupleDataSet.get().find("fake_Bs").Print();
tupleDataSet.plotOn(aFrame);

bFrame = tupleDataSet.get().find("true_Bs").frame();
tupleDataSet.get().find("true_Bs").Print();
tupleDataSet.plotOn(bFrame);

doubleCanvas = TCanvas();

doubleCanvas.Divide(2,1,0,0);
doubleCanvas.cd(1);

aFrame.Draw()

doubleCanvas.cd(2);
bFrame.Draw()

dirName = "tupleTestPlots";
currentTime = time.time();

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists(dirName)):
    os.mkdir(dirName)
os.chdir(dirName);
doubleCanvas.SaveAs("plot_%f.pdf" % currentTime);

raw_input("Press Enter to continue...")

from B2DXFitters.WS import WS
# for now, we're in the generation stage
#-config['Context'] = 'GEN'
#-genpdf = buildTimePdf(config)
import copy
# FIXME: need to deep-copy the config dictionary, and need to disable a few
# tweaks that speed up fitting during generation (because they waste time there)
genconfig = copy.deepcopy(config)
genconfig['Context'] = 'GEN'
genconfig['NBinsAcceptance'] = 0
genconfig['NBinsProperTimeErr'] = 0
genconfig['ParameteriseIntegral'] = False
genpdf = buildTimePdf(genconfig)
'''
#vim: sw=4:et
