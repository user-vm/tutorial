#!/bin/sh
# -*- mode: python; coding: utf-8 -*-
# vim: ft=python:sw=4:tw=78:expandtab
# --------------------------------------------------------------------------- 
# @file time-tut002.py
#
# @brief hands-on session example 2 (B2DXFitters workshop, Padova, 2015)
#
# average mistag, average sigma_t, spline acceptance
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
ulimit -v $((3072 * 1024))
ulimit -s $((   8 * 1024))

# trampoline into python
exec $schedtool /usr/bin/time -v env python -O "$0" - "$@"
"""
__doc__ = """ real docstring """
# -----------------------------------------------------------------------------
# Load necessary libraries
# -----------------------------------------------------------------------------
import B2DXFitters
import ROOT
from ROOT import RooFit

# user code starts here

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

# then read config dictionary from a file
from B2DXFitters.utils import configDictFromFile
config = configDictFromFile('time-conf002.py')

# start with RooFit stuff
from ROOT import ( RooRealVar, RooConstVar, RooCategory, RooWorkspace,
    RooArgSet, RooArgList, RooLinkedList, RooAbsReal, RooRandom, TRandom3
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
    
    mistag = WS(ws, RooRealVar('mistag', 'mistag', 0.35, 0.0, 0.5))
    tageff = WS(ws, RooRealVar('tageff', 'tageff', 0.60, 0.0, 1.0))
    timeerr = WS(ws, RooRealVar('timeerr', 'timeerr', 0.040, 0.001, 0.100))
    
    
    # now build the PDF
    from B2DXFitters.timepdfutils import buildBDecayTimePdf
    from B2DXFitters.resmodelutils import getResolutionModel
    from B2DXFitters.acceptanceutils import buildSplineAcceptance
    
    obs = [ qf, qt, time ]
    acc, accnorm = buildSplineAcceptance(ws, time, 'Bs2DsPi_accpetance',
            config['SplineAcceptance']['KnotPositions'],
            config['SplineAcceptance']['KnotCoefficients'][config['Context']],
            'FIT' in config['Context']) # float for fitting
    if 'GEN' in config['Context']:
        acc = accnorm # use normalised acceptance for generation
    # get resolution model
    resmodel, acc = getResolutionModel(ws, config, time, timeerr, acc)
    # build the time pdf
    pdf = buildBDecayTimePdf(
        config, 'Bs2DsPi', ws,
        time, timeerr, qt, qf, [ [ mistag ] ], [ tageff ],
        Gamma, DGamma, Dm,
        C = one, D = zero, Dbar = zero, S = zero, Sbar = zero,
        timeresmodel = resmodel, acceptance = acc)
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
ds = genpdf['pdf'].generate(RooArgSet(*genpdf['obs']), 15000, RooFit.Verbose())

ds.Print('v')
for o in genpdf['obs']:
    if not o.InheritsFrom('RooAbsCategory'): continue
    ds.table(o).Print('v')

# use workspace for fit pdf in such a simple fit
config['Context'] = 'FIT'
fitpdf = buildTimePdf(config)
# add data set to fitting workspace
ds = WS(fitpdf['ws'], ds)

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
rawfitresult = fitpdf['pdf'].fitTo(ds, fitOpts)

# pretty-print the result
from B2DXFitters.FitResult import getDsHBlindFitResult
result = getDsHBlindFitResult(config['IsData'], config['Blinding'],
    rawfitresult)
print result

# write raw fit result and workspace to separate ROOT files
from ROOT import TFile
f = TFile('fitresult002_%04d.root' % SEED, 'recreate')
f.WriteTObject(rawfitresult, 'fitresult002_%04d' % SEED)
f.Close()
del f
genpdf['ws'].writeToFile('workspace002_%04d.root' % SEED, True)
fitpdf['ws'].writeToFile('workspace002_%04d.root' % SEED, False)

# all done
