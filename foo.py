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
__doc__ = """ real docstring """
# -----------------------------------------------------------------------------
# Load necessary libraries
# -----------------------------------------------------------------------------
from ROOT import TFile, TTree, TChain, TH1D, TList, TCanvas

# custom
import B2DXFitters
from B2DXFitters.factory import get_title_from_mode, rescale_roofit_pad
from ROOT import (RooKResModel, Inverse, RooGaussEfficiencyModel,
                  RooCubicSplineFun)

# standard
from ROOT import (RooWorkspace, RooArgSet, RooArgList, RooFit,
                  RooRealVar, RooConstVar, RooRealConstant,
                  RooProduct, RooGaussModel, RooBDecay, RooDataSet,
                  RooBinning, RooPolyVar, RooProduct)

plotfile='foo.pdf'

# globals, and aliases
from ROOT import gPad, gStyle, gSystem, kRed, kBlue, kAzure, kGreen, kBlack
const = RooRealConstant.value

# setup
gStyle.SetOptStat('nemrou')
canvas = TCanvas('canvas', 'canvas', 800, 600)

## variables
time = RooRealVar('time', 'B_{s} decay time [ps]', 0.0, 15.0)
bins = 300
time.setBins(bins)
time.setBins(bins*3, 'cache')

gamma = RooRealVar('gamma', 'gamma', 0.661, 0., 3.)
dGamma = RooRealVar('dGamma', 'dGamma', -0.106, -3., 3.)
dM = RooRealVar('dM', 'dM', 17.768, 0.1, 20.)
one = const(1.)
zero = const(0.)
tau = Inverse('tau', 'tau', gamma)
# tauk = Inverse('tauk', 'tauk', kgamma)

## acceptance
spline_knots = [ 0.5, 1.0, 1.5, 2.0, 3.0, 12.0 ]
spline_coeffs = [ 0.03902e-01, 7.32741e-01, 9.98736e-01,
                  1.16514e+00, 1.25167e+00, 1.28624e+00 ]
assert(len(spline_knots) == len(spline_coeffs))

# knot binning
mode="Bs2DsPi"
knotbinning = RooBinning(time.getMin(), time.getMax(),
                         '{}_knotbinning'.format(mode))
for v in spline_knots:
    knotbinning.addBoundary(v)
knotbinning.removeBoundary(time.getMin())
knotbinning.removeBoundary(time.getMax())
oldbinning, lo, hi = time.getBinning(), time.getMin(), time.getMax()
time.setBinning(knotbinning, '{}_knotbinning'.format(mode))
time.setBinning(oldbinning)
time.setRange(lo, hi)
del knotbinning, oldbinning, lo, hi

# knot coefficients
coefflist = RooArgList()
for i, v in enumerate(spline_coeffs):
    coefflist.add(const(v))
i = len(spline_coeffs)
coefflist.add(one)
spline_knots.append(time.getMax())
spline_knots.reverse()
fudge = (spline_knots[0] - spline_knots[1]) / (spline_knots[2] - spline_knots[1])
lastmycoeffs = RooArgList()
lastmycoeffs.add(const(1. - fudge))
lastmycoeffs.add(const(fudge))
polyvar = RooPolyVar('{}_SplineAccCoeff{}'.format(mode, i), '',
                     coefflist.at(coefflist.getSize() - 2), lastmycoeffs)
coefflist.add(polyvar)
del i

# create the spline itself
tacc = RooCubicSplineFun('{}_SplineAcceptance'.format(mode), '', time,
                         '{}_knotbinning'.format(mode), coefflist)
del lastmycoeffs, coefflist

# resolution model with decay time resolution and acceptance
gresacc = RooGaussEfficiencyModel('{}_GaussianWithPEDTE'.format(tacc.GetName()),
                               '', time, tacc, const(0.0), const(0.044))
# perfect decay time resolution
gres = RooGaussModel('{}_GaussianWithPEDTE'.format('noacc'),
                               '', time, const(0.0), const(0.0001))
# finite decay time resolution (44 fs)
gresdt = RooGaussModel('{}_GaussianWithPEDTE'.format('noaccdt'),
                               '', time, const(0.0), const(0.044))

# perfect
model0 = RooBDecay('model0', 'model', time, tau, dGamma,
                   one, zero, const(1.), zero, dM, gres, RooBDecay.SingleSided)
# finite decay time resolution
model1 = RooBDecay('model1', 'model', time, tau, dGamma,
                   one, zero, const(1.), zero, dM, gresdt, RooBDecay.SingleSided)
# +mistag (average mistag of omega = .35, 100% tagging efficiency)
model2 = RooBDecay('model2', 'model', time, tau, dGamma,
                   one, zero, const(1.-2*.35), zero, dM, gresdt, RooBDecay.SingleSided)
# + acceptance
model3 = RooBDecay('model3', 'model', time, tau, dGamma,
                   one, zero, const(1.-2*.35), zero, dM, gresacc, RooBDecay.SingleSided)

# plot ideal
tfr = time.frame()
model0.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''))
tfr.Draw()
canvas.Print('foo-perfect.pdf')
# plot with time resolution
tfr = time.frame()
model0.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''), RooFit.Invisible())
model1.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''))
tfr.Draw()
canvas.Print('foo-dt.pdf')
# + mistag 
#resol.setVal(0.044)
tfr = time.frame()
model0.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''), RooFit.Invisible())
model2.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''))
tfr.Draw()
canvas.Print('foo-mistag-dt.pdf')
# switch acceptance on
tfr = time.frame()
model0.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''), RooFit.Invisible())
model3.plotOn(tfr, RooFit.Precision(1e-5), RooFit.Name(''))
tfr.Draw()
canvas.Print('foo-all-dirt-effects.pdf')
