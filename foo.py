#!/usr/bin/python
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
resol.setVal(0.044)
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
