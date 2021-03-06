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
from ROOT import TFile, RooFit, TTree, RooDataSet, RooArgSet, RooRealVar, TCanvas, RooWorkspace
from B2DXFitters.WS import WS
import sys,os,time

def buildTimePdf(config, tupleDataSet, tupleDict):

    from B2DXFitters.WS import WS
    print 'CONFIGURATION'
    for k in sorted(config.keys()):
        print '    %32s: %32s' % (k, config[k])

    ws = RooWorkspace('ws_%s' % config['Context'])
    one = WS(ws, RooConstVar('one', '1', 1.0))
    zero = WS(ws, RooConstVar('zero', '0', 0.0))
    ###USE FIT CONTEXT
    """
    build time pdf, return pdf and associated data in dictionary
    """
    # start by defining observables
    time = WS(ws, tupleDataSet.get().find('ct'));
    #qt = WS(ws, tupleDataSet.get().find('ssDecision'));
    '''
    time = WS(ws, RooRealVar('time', 'time [ps]', 0.2, 15.0))
    '''
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
    tageff = WS(ws, RooRealVar('tageff', 'tageff', 0.60, 0.0, 1.0))
    terrpdf = WS(ws, tupleDataSet.get().find('cterr'));
    timeerr = WS(ws, RooRealVar('timeerr', 'timeerr', 0.040, 0.001, 0.100))
    #MISTAGPDF
    # fit average mistag
    # add mistagged 
    #ge rid of untagged events by putting restriction on qf or something when reduceing ds
    # now build the PDF
    from B2DXFitters.timepdfutils import buildBDecayTimePdf
    from B2DXFitters.resmodelutils import getResolutionModel
    from B2DXFitters.acceptanceutils import buildSplineAcceptance
    
    obs = [ qf, qt, time]
    acc, accnorm = buildSplineAcceptance(ws, time, 'Bs2DsPi_accpetance',
            config['SplineAcceptance']['KnotPositions'],
            config['SplineAcceptance']['KnotCoefficients'][config['Context'][0:3]],
            'FIT' in config['Context']) # float for fitting
    # get resolution model
    resmodel, acc = getResolutionModel(ws, config, time, timeerr, acc)
    mistagpdf = WS(ws,RooArgList(tupleDataSet.get().find('ssMistag'),tupleDataSet.get().find('osMistag')));#???
    '''
    if 'GEN' in config['Context']:
        # build a (mock) mistag distribution
        mistagpdfparams = {} # start with parameters of mock distribution
        for sfx in ('omega0', 'omegaavg', 'f'):
            mistagpdfparams[sfx] = WS(ws, RooRealVar(
                    'Bs2DsPi_mistagpdf_%s' % sfx, 'Bs2DsPi_mistagpdf_%s' % sfx,
                    config['TrivialMistagParams'][sfx]))
        # build mistag pdf itself
        mistagpdf = WS(ws, [tupleDataSet.reduce('ssMistag'), tupleDataSet.reduce('osMistag')]);
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
            timeresmodel = resmodel, acceptance = acc, timeerrpdf,
            mistagpdf = [mistagpdf], mistagobs = eta)
    else:
        pdf = buildBDecayTimePdf(
            config, 'Bs2DsPi', ws,
            time, timeerr, qt, qf, [ [ eta ] ], [ tageff ],
            Gamma, DGamma, Dm,
            C = one, D = zero, Dbar = zero, S = zero, Sbar = zero,
            timeresmodel = resmodel, acceptance = acc, timeerrpdf = None)
    '''

    
    pdf = buildBDecayTimePdf(
        config, 'Bs2DsPi', ws,
        time, timeerr, qt, qf, [ [ eta ] ], [ tageff ],
        Gamma, DGamma, Dm,
        C = one, D = zero, Dbar = zero, S = zero, Sbar = zero,
        timeresmodel = resmodel, acceptance = acc, timeerrpdf = terrpdf,
        mistagpdf = [mistagpdf], mistagobs = eta)
    
    return { # return things
            'ws': ws,
            'pdf': pdf,
            'obs': obs
            }

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
if 'r' in sys.argv:
    #print "WRONG"
    #sys.exit(1);

    if not os.path.isfile(tupleDictFilename) or tupleDictFilename == "-":
        print "Filename argument invalid; running for default tuple dictionary file"
        tupleDictFilename = os.environ["B2DXFITTERSROOT"] + "/tutorial/tupleDict2.py"

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

    #tupleDataSet = RooDataSet("treeData","treeData",tree1,RooArgSet(*varList));
    
    weightvar = RooRealVar("weight", "weight", -1e7, 1e7)
    tupleDataSet = RooDataSet("tupleDataSet", "tupleDataSet",
        RooArgSet(*varList),
        RooFit.Import(tree1), RooFit.WeightVar(weightvar))
    
    ws = RooWorkspace('ws_FIT')
    tupleDataSet = WS(ws, tupleDataSet, varRenamedList)

    tupleDataSet.Print();
    sys.exit(0);
    #qt needs to be a category?
    # Manuel's shit...
    #weightvar = RooRealVar("weight", "weight", -1e7, 1e7)
    #tupleDataSet = RooDataSet("tupleDataSet", "tupleDataSet",
    #    RooArgSet(treetime, treeqt, treeqf, treeeta),
    #    RooFit.Import(tree1), RooFit.WeightVar(weightvar))
    #tupleDS = WS(ws, tupleDS, [
    #    RooFit.RenameVariable("Bs_ctau", "time"), ... ])
    # # note: do not forget to add to fitTo options: RooFit.SumW2Error(True)
    #ROOT.SetOwnership(tupleDataSet,False);

    #tupleDataSet.get().find(varName).Print();
    '''
    for i in range(len(tupleDict)):
        varName = tupleDict.keys()[i];
        a = tupleDataSet.get().find(varName);
        a.SetName(tupleDict[varName]);
        a.SetTitle(tupleDict[varName]);
    
    from ROOT import TFile
    import time
    g = TFile('../BsStuff.root', 'recreate')
    g.WriteTObject(tupleDataSet)
    g.Close()
    del g'''

else:
    print "Running without 'r' argument disabled" 
    sys.exit(0);
    rootInFile = TFile("../BsStuff.root");
    keyList = rootInFile.GetListOfKeys();
    keyList.At(0).ReadObj().Print();
    keyList.At(1).ReadObj().Print();
    tupleDataSet = rootInFile.Get('treeData');

    if not os.path.isfile(tupleDictFilename) or tupleDictFilename == "-":
        print "Filename argument invalid; running for default tuple dictionary file"
        tupleDictFilename = os.environ["B2DXFITTERSROOT"] + "/tutorial/tupleDict2.py"
    
    tupleDict = importTupleDict(tupleDictFilename);
    tupleDataSet = tupleDataSet.reduce('osDecision==ssDecision');
    
    from B2DXFitters.utils import configDictFromFile
    config = configDictFromFile('bsConfig.py');

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
    
    from B2DXFitters.WS import WS
    fitpdf = buildTimePdf(config, tupleDataSet, tupleDict);
    ws = fitpdf['ws'];
    tupleDataSet = WS(ws, tupleDataSet);

    # set constant what is supposed to be constant
    from B2DXFitters.utils import setConstantIfSoConfigured
    setConstantIfSoConfigured(config, fitpdf['pdf'])

    # set up fitting options
    fitopts = [ RooFit.Timer(), RooFit.Save(),
        RooFit.Strategy(config['FitConfig']['Strategy']),
        RooFit.Optimize(config['FitConfig']['Optimize']),
        RooFit.Offset(config['FitConfig']['Offset']),
        RooFit.NumCPU(config['FitConfig']['NumCPU']) ]

    # set up blinding for data
    fitopts.append(RooFit.Verbose(not (config['IsData'] and config['Blinding'])))
    if config['IsData'] and config['Blinding']:
        from ROOT import RooMsgService
        RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)                                                                                                                             
        fitopts.append(RooFit.PrintLevel(-1))
    fitOpts = RooLinkedList()
    for o in fitopts: fitOpts.Add(o)

    # fit
    rawfitresult = fitpdf['pdf'].fitTo(tupleDataSet, fitOpts)

    # pretty-print the result
    from B2DXFitters.FitResult import getDsHBlindFitResult
    result = getDsHBlindFitResult(config['IsData'], config['Blinding'],
        rawfitresult)
    print result

    '''
    doubleCanvas = TCanvas();
        
    frameList = []
    print '\n\n',tupleDict.values(),'\n\n'

    doubleCanvas.Divide(3,3,0,0)

    for i in range(len(tupleDict)):
        #varName = tupleDict.keys()[i];
        frameList += [tupleDataSet.get().find(tupleDict.values()[i]).frame()];
        tupleDataSet.plotOn(frameList[i], RooFit.DrawOption('b'));
        doubleCanvas.cd(i+1);
        frameList[i].Draw();
    '''
    for i in range(len(tupleDict)):
        tupleDataSet.get().find(tupleDict.values()[i]).Print();
    sys.exit(0);
    '''
    doubleCanvas.Update();
    raw_input('Press Enter to continue');
    #doubleCanvas.Clear();
    #print tupleDict.keys()[i];
    #a.Print();
    #print
    doubleCanvas.Close();'''

tupleDataSet.Print();

sys.exit(0);

dirName = "tupleTestPlots";
currentTime = time.time();

os.chdir(os.environ['B2DXFITTERSROOT']+'/tutorial');
if(not os.path.exists(dirName)):
    os.mkdir(dirName)
os.chdir(dirName);
doubleCanvas.SaveAs("plot_%f.pdf" % currentTime);

raw_input("Press Enter to continue...")
'''
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
