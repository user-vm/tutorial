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
NUMCAT = 1
import time
TIME_NOW = str(time.time())

def drawDsPlot(ds,catNum = 0):

    from ROOT import RooAbsData,TCanvas

    etaHist = RooAbsData.createHistogram(ds,'eta',100);
    theCanvas = TCanvas('dsCanvas','Eta histogram (category' + str(catNum) + ')' )
    etaHist.Draw("hist PFC");
    theCanvas.SaveAs("etaCat"+str(catNum)+"Hist"+TIME_NOW+".pdf");
    #s = raw_input("Press Enter to continue...");
    theCanvas.Close();

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
    
    #etaSet = RooDataSet('etaSet','etaSet',ds,RooArgSet(ds.get().find['eta']));
    #etaSet.Print();
    #etaHist.SetAxisRange(0.1,0.2);
    #etaHist.SetAxisRange(0.1,0.3);

    from ROOT import TCanvas

    histCanvas = TCanvas();

    ROOT.gStyle.SetPalette(ROOT.kOcean);
    
    #create stack to contain the chopped TH1Ds
    #etaHistStack = THStack("etaHistStack", "Distribution of #eta;#eta;number of pseudo-experiments");

    limList += [etaHist.GetNbinsX()];
    histCutterFunc = TF1("histCutterFunc","((x>=[0])?((x<[1])?1:0):0)",0.0,1.0);

    etaMax = etaHist.GetMaximum();
    print etaMax

    cloneList = []

    etaHist.GetYaxis().SetRangeUser(0,etaMax*1.05);
    
    etaHist.SetLineColor(ROOT.kWhite);
    etaHist.Draw("histSame");
    etaHist.SetTitle('Distribution of #eta (toy)')
    etaHist.GetXaxis().SetTitle('#eta')

    for i in range(len(limList)-1):
        
        cloneList = [etaHist.Clone()];
        #etaHistClone.SetBins(limList[i+1]-limList[i],etaHist.GetBinContent(limList[i]),etaHist.GetBinContent(limList[i+1]));
        histCutterFunc.SetParameter(0,etaHist.GetXaxis().GetBinCenter(limList[i]));
        histCutterFunc.SetParameter(1,etaHist.GetXaxis().GetBinCenter(limList[i+1]));
        cloneList[-1].Multiply(histCutterFunc);
        cloneList[-1].SetFillColor(38+i);
        cloneList[-1].SetLineColor(ROOT.kBlack);
        if i==0:
            cloneList[-1].GetYaxis().SetRangeUser(0,etaMax*1.05);
        cloneList[-1].Draw("histSAME");
        #etaHistStack.Add(etaHistClone);

    #etaHistStack.Draw();
    histCanvas.Update();
    histCanvas.SaveAs('catHist%d.pdf' % SEED);
    s = raw_input("Press Enter to continue...");
    sys.exit(0);    

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
#ds.Print();
#sys.exit(0);
#saveEta(ds);

# HACK (2/2): restore correct eta range after generation
ds.get().find('eta').setRange(0.0, 0.5)

ds.Print('v')
for o in genpdf['obs']:
    if not o.InheritsFrom('RooAbsCategory'): continue
    ds.table(o).Print('v')

from ROOT import RooDataSet, RooArgSet

from ROOT import TList

mistagresultList = TList();
etaAvgList = TList();
print "**** ADDING CATEGORIES ****"
ds = ds.reduce("qt!=qt::Untagged");
xRegions = createCategoryHistogram(ds,ds.get().find('eta'),NUMCAT);
ds.addColumn(xRegions)
ds.table(xRegions).Print("v")

keepvars = [ds.get().find(name) for name in ['qt', 'qf', 'tageffRegion', 'time']]

for i in xrange(NUMCAT):
    etaAvgList.AddLast(ds.reduce("tageffRegion == tageffRegion::Cat%u" % (i + 1,)).meanVar(ds.get().find('eta')));

etaAvg = ds.meanVar(ds.get().find('eta'));

dspercat = [ ds.reduce(RooArgSet(*keepvars),"tageffRegion == tageffRegion::Cat%u" % (i + 1,)) for i in xrange(NUMCAT) ]

i = 0
for dspc in dspercat:
    print "**** CAT %u ****" % i
    i = i + 1
    dspc.Print("v")

#drawDsPlot(ds)

from math import sqrt
import random
#random.seed(SEED);

genEtaList = TList();

for i in xrange(NUMCAT):
    
    # use workspace for fit pdf in such a simple fit
    fitconfig = copy.deepcopy(config1)
    fitconfig['Context'] = 'FIT%u' % i
    fitconfig['NBinsAcceptance'] = 0

    fitpdf = buildTimePdf(fitconfig)
    #ds = WS(fitpdf['ws'],ds);
    # add data set to fitting workspace
    ds1 = WS(fitpdf['ws'], dspercat[i])

    print 72 * "#"
    print "WS:" + str(fitpdf["ws"])
    print "PDF:" + str(fitpdf["pdf"])
    print "OBS:" + str(fitpdf["obs"])
    print "DS:" + str(ds1)
    fitpdf['ws'].Print("v")
    fitpdf['pdf'].Print("v")
    ds1.Print("v")
    mistag = fitpdf['ws'].obj("mistag")
    aveta = etaAvgList.At(i).getValV();
    mistag.setVal(aveta);
    mistag.setError(min([0.5 / NUMCAT / sqrt(12), abs(aveta) * 0.5, abs(aveta - 0.5) * 0.5]))
    mistag.Print("v")
    print 72 * "#"

    print "\n-------PRINTING DS1--------\n"
    ds1.Print('v')
    for o in fitpdf['obs']:
        if not o.InheritsFrom('RooAbsCategory'): continue
        ds1.table(o).Print('v')
    print "\n---------------------------\n"

    """
    etaLow = ROOT.Double(0.0);
    etaHigh = ROOT.Double(0.5);
    ds1.getRange(ds1.get().find('eta'),etaLow,etaHigh);
    ds1.get().find('eta').setRange(etaLow, etaHigh)
    """
    

    #drawDsPlot(ds1,i);
    #etaAvg = ds.meanVar(ds.get().find('eta'));
    print "\n\n\nETA = ",ds.meanVar(ds.get().find('eta')).getValV(),"\n\n\n\n";
    #raw_input('Press Enter to continue');

    # set constant what is supposed to be constant
    from B2DXFitters.utils import setConstantIfSoConfigured
    setConstantIfSoConfigured(fitconfig, fitpdf['pdf'])

    # set up fitting options
    fitopts = [ RooFit.Timer(), RooFit.Save(),
                RooFit.Strategy(fitconfig['FitConfig']['Strategy']),
                RooFit.Optimize(fitconfig['FitConfig']['Optimize']),
                RooFit.Offset(fitconfig['FitConfig']['Offset']),
                RooFit.NumCPU(fitconfig['FitConfig']['NumCPU']) ]

    # set up blinding for data
    fitopts.append(RooFit.Verbose(not (fitconfig['IsData'] and fitconfig['Blinding'])))
    if fitconfig['IsData'] and fitconfig['Blinding']:
        from ROOT import RooMsgService
        RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)                                                                                                                             
        fitopts.append(RooFit.PrintLevel(-1))
    fitOpts = RooLinkedList()
    for o in fitopts: fitOpts.Add(o)
    
    # fit
    rawfitresult = fitpdf['pdf'].fitTo(ds1, fitOpts)
    #p0End = rawfitresult.floatParsFinal().find('Bs2DsPi_mistagcalib_p0');
    #p1End = rawfitresult.floatParsFinal().find('Bs2DsPi_mistagcalib_p1');
    genEtaList.AddLast(rawfitresult.floatParsFinal().find('eta'));
    '''print "\n\n\nbleah\n",rawfitresult.floatParsFinal().Print(),"\n\nboh\n\n\n\n";
    '''
    # pretty-print the result
    from B2DXFitters.FitResult import getDsHBlindFitResult
    result = getDsHBlindFitResult(fitconfig['IsData'], fitconfig['Blinding'],
        rawfitresult)
    print 'RESULT',result
    rawfitresult.floatParsFinal().Print()

ds.get().Print();
'''
for i in range(mistagresultList.GetSize()):

    print "mistag =",mistagresultList.At(i).getValV(),"+-",mistagresultList.At(i).getError(), ", avg. eta =",etaAvgList.At(i).getValV(),"+-",etaAvgList.At(i).getError()
'''

print 'GENETALIST'
genEtaList.Print();

print 'ETAAVG'
etaAvg.Print();

print 'ETAAVGLIST'
etaAvgList.Print();
sys.exit(0);
from ROOT import TFile
g = TFile('fitresultlist123/fitresultlist123_%04d.root' % SEED, 'recreate')
#g.WriteTObject(p0End, 'fitresultlist123/fitresultlist123003_%04d' % SEED)
#g.WriteTObject(p1End, 'fitresultlist123/fitresultlist123003_%04d' % SEED)
g.WriteTObject(genEtaList,'fitresultlist123/fitresultlist123003_%04d' % SEED)
g.WriteTObject(etaAvg, 'fitresultlist123/fitresultlist123003_%04d' % SEED)
g.WriteTObject(etaAvgList, 'fitresultlist123/fitresultlist123003_%04d' % SEED)
g.Close()
del g

#import sys
#sys.exit(0);
"""
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
g.WriteTObject(rawfitresultList, 'fitresultlist/fitresultlist003_%04d' % SEED)
g.WriteTObject(etaAvgValVarList, 'fitresultlist/fitresultlist003_%04d' % SEED)
g.Close()
del g"""

# all done
