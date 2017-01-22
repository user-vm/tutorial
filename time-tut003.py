#!/bin/sh
# -*- mode: python; coding: utf-8 -*-
# vim: ft=python:sw=4:tw=78:expandtab
# --------------------------------------------------------------------------- 
# @file time-tut003.py
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
import numpy as n
import B2DXFitters
import ROOT
from ROOT import RooFit
#from ROOT import TBrowser
#from B2DXFitters.setCategories import setCategories
#from B2DXFitters.createCategoryHistogram import createCategoryHistogram

# user code starts here

#number of tagging categories to use
NUMCAT = 5;

def drawDsPlot(ds):

    from ROOT import RooAbsData

    etaHist = RooAbsData.createHistogram(ds,'eta',100);
    etaHist.Draw("hist PFC");
    s = raw_input("Press Enter to continue...");

# histogram creation function, moved here to avoid recompilation-----

def createCategoryHistogram(ds,x,numCat,categoryList = None):

    from ROOT import RooAbsData, RooDataSet, RooPrintable, RooThresholdCategory, THStack, TF1
    from ROOT.Math import GaussIntegrator
    import ROOT

    if categoryList==None:
        categoryList = []
        for i in range(numCat):
            categoryList += ["Cat"+str(i+1)]

    etaHist = RooAbsData.createHistogram(ds,'eta',100);

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
    
    xRegions = RooThresholdCategory("tageffRegion", "region of tageff", x, categoryList[numCat-1]);

    for i in range(0,numCat-1):
        xRegions.addThreshold(etaHist.GetXaxis().GetBinCenter(limList[i+1]),categoryList[i]);

    xRegions.writeToStream(ROOT.cout,False);
    xRegions.writeToStream(ROOT.cout,True);
    '''
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
    s = raw_input("Press Enter to continue...");'''
    
    return xRegions#,x

def saveEta(g, numBins = 100):
    
    from ROOT import TFile, RooAbsData
    import os
    if not os.path.isdir('etaHist'):
        os.makedirs('etaHist');
    os.chdir('etaHist');
    etaHist = RooAbsData.createHistogram(g,'eta',100);
    f = TFile('etaHist003_%04d.root' % SEED, 'recreate')
    etaHist.Write('etaHist')
    f.Close()
    del f

#------------------------------------------------------------

# start by getting seed number
import sys
SEED = None
for tmp in sys.argv[1:]:
    try:
        SEED = int(tmp)
    except ValueError:
        print ('DEBUG: argument %s is no number, trying next argument as'
            'seed') % tmp
if None == SEED:
    print 'ERROR: no seed given'
    sys.exit(1)

#DELET THIS
#SEED = 42

# then read config dictionary from a file
from B2DXFitters.utils import configDictFromFile
config = configDictFromFile('time-conf003.py')
config1 = configDictFromFile('fit-time-conf003.py')
print config
#config['MistagCalibParams']['etaavg']=0.2
#config['TrivialMistagParams']['omegaavg']=0.2
#print config
#import sys
#sys.exit(0)

# start with RooFit stuff
from ROOT import ( RooRealVar, RooConstVar, RooCategory, RooWorkspace,
    RooArgSet, RooArgList, RooLinkedList, RooAbsReal, RooRandom, TRandom3,
    MistagDistribution, MistagCalibration, RooFormulaVar
    )
# safe settings for numerical integration (if needed)
RooAbsReal.defaultIntegratorConfig().setEpsAbs(1e-9)
RooAbsReal.defaultIntegratorConfig().setEpsRel(1e-9)
RooAbsReal.defaultIntegratorConfig().getConfigSection(
    'RooAdaptiveGaussKronrodIntegrator1D').setCatLabel('method','15Points')
RooAbsReal.defaultIntegratorConfig().getConfigSection(
    'RooAdaptiveGaussKronrodIntegrator1D').setRealValue('maxSeg', 1000)
RooAbsReal.defaultIntegratorConfig().method1D().setLabel(
    'RooAdaptiveGaussKronrodIntegrator1D')
RooAbsReal.defaultIntegratorConfig().method1DOpen().setLabel(
    'RooAdaptiveGaussKronrodIntegrator1D')

# seed the Random number generator
rndm = TRandom3(SEED + 1)
RooRandom.randomGenerator().SetSeed(int(rndm.Uniform(4294967295)))
del rndm

# as things become more complicated, it's useful to have "build-it-all"
# routine, which works for both generation and fitting; this also allows for
# easier setups of scenarios where you build with one pdf and fit with a
# different one (e.g. per-event mistag in generation, average in fit to see
# the gain in sensitivity from the per-event mistag)
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
    eta = WS(ws, RooRealVar('eta', 'eta', 0.35,
        0.0 if 'FIT' in config['Context'] else (1. + 1e-5) * max(0.0,
        config['TrivialMistagParams']['omega0']), 0.5))
    tageff = WS(ws, RooRealVar('tageff', 'tageff', 0.60, 1.0, 1.0))
    timeerr = WS(ws, RooRealVar('timeerr', 'timeerr', 0.040, 0.001, 0.100))
    # fit average mistag
    # add mistagged 
    #ge rid of untagged events by putting restriction on qf or something when reduceing ds
    # now build the PDF
    from B2DXFitters.timepdfutils import buildBDecayTimePdf
    from B2DXFitters.resmodelutils import getResolutionModel
    from B2DXFitters.acceptanceutils import buildSplineAcceptance
    
    obs = [ qf, qt, time, eta ]
    acc, accnorm = buildSplineAcceptance(ws, time, 'Bs2DsPi_accpetance',
            config['SplineAcceptance']['KnotPositions'],
            config['SplineAcceptance']['KnotCoefficients'][config['Context']],
            'FIT' in config['Context']) # float for fitting
    if 'GEN' in config['Context']:
        acc = accnorm # use normalised acceptance for generation
    # get resolution model
    resmodel, acc = getResolutionModel(ws, config, time, timeerr, acc)
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
    # build mistag calibration DELETE THIS LATER
    mistagcalibparams = {} # start with parameters of calibration
    for sfx in ('p0', 'p1', 'etaavg'):
        mistagcalibparams[sfx] = WS(ws, RooRealVar(
            'Bs2DsPi_mistagcalib_%s' % sfx, 'Bs2DsPi_mistagpdf_%s' % sfx,
            config['MistagCalibParams'][sfx]))
    for sfx in ('p0', 'p1'): # float calibration paramters
        mistagcalibparams[sfx].setConstant(False)
        mistagcalibparams[sfx].setError(0.1)
    # build mistag pdf itself
    omega = WS(ws, MistagCalibration(
        'Bs2DsPi_mistagcalib', 'Bs2DsPi_mistagcalib',
        eta, mistagcalibparams['p0'], mistagcalibparams['p1']))#,
        #mistagcalibparams['etaavg']))

    # build the time pdf
    pdf = buildBDecayTimePdf(
        config, 'Bs2DsPi', ws,
        time, timeerr, qt, qf, [ [ omega ] ], [ tageff ],
        Gamma, DGamma, Dm,
        C = one, D = zero, Dbar = zero, S = zero, Sbar = zero,
        timeresmodel = resmodel, acceptance = acc, timeerrpdf = None,
        mistagpdf = [ mistagpdf ], mistagobs = eta)
    return { # return things
            'ws': ws,
            'pdf': pdf,
            'obs': obs
            }

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

# generate 15K events
print '150K'
ds = genpdf['pdf'].generate(RooArgSet(*genpdf['obs']), 150000, RooFit.Verbose())
#saveEta(ds);

#import sys
#sys.exit(0);
#print "Wrong";

# HACK (2/2): restore correct eta range after generation
ds.get().find('eta').setRange(0.0, 0.5)
#t = TBrowser('Your waifu is shit',ds.get(1).find('eta'));
#s = raw_input("Press Enter to quit");
#sys.exit(0);

ds.Print('v')
for o in genpdf['obs']:
    if not o.InheritsFrom('RooAbsCategory'): continue
    ds.table(o).Print('v')

from ROOT import RooDataSet, RooArgSet

from ROOT import TList
rawfitresultList = TList();
p0List = TList();
p1List = TList();

xRegions = createCategoryHistogram(ds,ds.get().find('eta'),NUMCAT);
ds.addColumn(xRegions)

#config['MistagCalibParams']['etaavg']=0.2
#config['TrivialMistagParams']['omegaavg']=0.2
#drawDsPlot(ds)

for i in range(NUMCAT):

    # use workspace for fit pdf in such a simple fit
    config1['Context'] = 'FIT'
    config1['NBinsAcceptance'] = 0
    config1['MistagCalibParams']['etaavg']= ds.meanVar(ds.get().find('eta')).getValV();
    config1['TrivialMistagParams']['omegaavg']= ds.meanVar(ds.get().find('eta')).getValV();

    fitpdf = buildTimePdf(config1)
    # add data set to fitting workspace
    ds1 = WS(fitpdf['ws'], ds.reduce("tageffRegion==tageffRegion::Cat"+str(i+1)+"&&qt!=qt::Untagged"))
    fitpdf['ws'].var('tageff').setVal(1.0);
    fitpdf['ws'].var('tageff').setMax(1.0);
    fitpdf['ws'].var('tageff').setMin(1.0);
    print "\n-------PRINTING DS1--------\n"
    ds1.Print('v')
    for o in genpdf['obs']:
        if not o.InheritsFrom('RooAbsCategory'): continue
        ds1.table(o).Print('v')
    print "\n---------------------------\n"
    #drawDsPlot(ds1)

    # set constant what is supposed to be constant
    from B2DXFitters.utils import setConstantIfSoConfigured
    setConstantIfSoConfigured(config1, fitpdf['pdf'])

    # set up fitting options
    fitopts = [ RooFit.Timer(), RooFit.Save(),
                RooFit.Strategy(config1['FitConfig']['Strategy']),
                RooFit.Optimize(config1['FitConfig']['Optimize']),
                RooFit.Offset(config1['FitConfig']['Offset']),
                RooFit.NumCPU(config1['FitConfig']['NumCPU']) ]

    # set up blinding for data
    fitopts.append(RooFit.Verbose(not (config1['IsData'] and config1['Blinding'])))
    if config1['IsData'] and config1['Blinding']:
        from ROOT import RooMsgService
        RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)                                                                                                                             
        fitopts.append(RooFit.PrintLevel(-1))
    fitOpts = RooLinkedList()
    for o in fitopts: fitOpts.Add(o)

    # fit
    rawfitresult = fitpdf['pdf'].fitTo(ds1, fitOpts)
    rawfitresultList.AddLast(rawfitresult.floatParsFinal().find('tageff'));
    p0List.AddLast(rawfitresult.floatParsFinal().find('Bs2DsPi_mistagcalib_p0'));
    p1List.AddLast(rawfitresult.floatParsFinal().find('Bs2DsPi_mistagcalib_p1'));
    print "\n\n\nbleah\n",rawfitresult.floatParsFinal().Print(),"\n\nboh\n\n\n\n";
    # pretty-print the result
    from B2DXFitters.FitResult import getDsHBlindFitResult
    result = getDsHBlindFitResult(config1['IsData'], config1['Blinding'],
        rawfitresult)
    print result

ds.get().Print();

#import sys
#sys.exit(0);

#print the tageff, average eta, p0 and p1 values and errors, and save them as TLists of RooAbsArg
etaAvgValVarList = TList()

print "Tageff, avg. eta, p0, p1 (for each category):"

for i in range(rawfitresultList.GetSize()):

    etaAvgValVarList.AddLast(ds.meanVar(ds.get().find('eta'),"tageffRegion==tageffRegion::Cat"+str(i+1)))
    print "tageff =", rawfitresultList.At(i).getValV(),"+-",rawfitresultList.At(i).getError(),", etaAvg=", etaAvgValVarList.At(i).getValV(), "+-", etaAvgValVarList.At(i).getError(), ", p0 =", p0List.At(i).getValV(), "+-", p0List.At(i).getError(), ", p1 =", p1List.At(i).getValV(), "+-", p1List.At(i).getError()

#raw_input("Press Enter to continue");

#write fit result list to file
from ROOT import TFile
g = TFile('fitresultlist/fitresultlist_%04d.root' % SEED, 'recreate')
g.WriteTObject(p1List, 'fitresultlist/fitresultlist003_%04d' % SEED)
g.WriteTObject(p0List, 'fitresultlist/fitresultlist003_%04d' % SEED)
g.WriteTObject(rawfitresultList, 'fitresultlist/fitresultlist003_%04d' % SEED)
g.WriteTObject(etaAvgValVarList, 'fitresultlist/fitresultlist003_%04d' % SEED)
g.Close()
del g

import sys
sys.exit(0)
#-----------------------------------------------------------------------
#ENDS HERE
#-----------------------------------------------------------------------
#in case you want to plot the tageff vs eta

from ROOT import TGraphErrors, TGraph
import time

theCanvas = TCanvas();
#img = TImage.Create();
tageffVsEtaGraph = TGraphErrors(rawfitresultList.GetSize(),etaAvgValList,tageffValVList,etaAvgErrorList,tageffErrorList);
tageffVsEtaGraph.Draw("ap");
#ROOT.gSystem.ProcessEvents();
#img.FromPad(theCanvas);

theCanvas.Print("tageffVsEtaGraph_%f.pdf" % time.time(),"pdf");
#gSystem->ProcessEvents();

del theCanvas;

'''
# write raw fit result and workspace to separate ROOT files
from ROOT import TFile
f = TFile('fitresult003_%04d.root' % SEED, 'recreate')
f.WriteTObject(rawfitresult, 'fitresult003_%04d' % SEED)
f.Close()
del f
genpdf['ws'].writeToFile('workspace003_%04d.root' % SEED, True)
fitpdf['ws'].writeToFile('workspace003_%04d.root' % SEED, False)'''

# all done
