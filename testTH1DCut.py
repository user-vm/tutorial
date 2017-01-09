import ROOT
from ROOT import TH1D, TCanvas, TF1

c = TCanvas();
aTF1 = TF1("f1","sin(x)",0.0,1.0);
aTH1D = TH1D("penis","penis",100,0.0,1.0);
anotherTH1D = TH1D("vagina","vagina",50,0.0,0.5);
aTH1D.FillRandom("f1");
aTH1D.Draw();
anotherTH1D.FillRandom(aTH1D);
anotherTH1D.Draw();

s = raw_input("Press Enter to continue");
