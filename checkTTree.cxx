#include "TTree.h"
#include "TFile.h"
#include <iostream>

using namespace RooFit;

void tree3AddBranch() {
    //TFile *f = new TFile("../data_Bs2Dspipipi_11_final_sweight.root", "READ");
    TFile *f = new TFile("../Bs2Dspipipi_MC_fullSel_reweighted_combined.root", "READ");
    //TFile *g = new TFile("../data_Bs2Dspipipi_11_final_sweight_NO_SHORT_T.root", "RECREATE");
    TFile *g = new TFile("../Bs2Dspipipi_MC_fullSel_reweighted_combined_NO_SHORT_T.root", "READ");   
    Int_t new_K;
    Int_t new_nK;
    Short_t qtnK;
	Short_t qtK;
    TTree *t3 = (TTree*)f->Get("DecayTree");
    t3->SetBranchAddress("Bs_SS_nnetKaon_DEC", &qtnK);
    t3->SetBranchAddress("Bs_SS_Kaon_DEC", &qtK);
    //t3->Branch("corrKQT", &new_K, "corrKQT/D");
    //t3->Branch("corrnnetKQT", &new_nK, "corrnnetKQT/D");
    TTree *ntr = (TTree*)g->Get("DecayTree");
    //ntr = t3;
    ntr->SetBranchAddress("corrKQT", &new_K);
    ntr->SetBranchAddress("corrnnetKQT", &new_nK);
    Long64_t nentries = t3->GetEntries(); // read the number of entries in the t3
    Int_t wrongs = 0;
    for (Long64_t i = 0; i < nentries; i++) {
        t3->GetEvent(i);
        ntr->GetEvent(i);
        if (qtnK!=new_nK || qtK!=new_K){
            cout<<"   qtnK="<<qtnK<<"   new_nK="<<new_nK<<"   qtK="<<qtK<<"   new_K="<<new_K<<"\n";
            wrongs++;}
        /*if ((i+1)%100==1 && i!=0){
            cout<<i+1<<" / "<<nentries<<"\n";}//<< qtK<<"  qtnK="<<qtnK;
        new_K = qtK;
        new_nK = qtnK;*/
        //kBranch->Fill();
        //nkBranch->Fill();
        //ntr->Fill();

        //cout<<"ntr num entries    "<<ntr->GetEntries()<<"\n";
        //cout<<"  new_K="<<new_K<<"  new_nK="<<new_nK<<"\n";
    }

	//ntr->Fill();

    cout<<wrongs<<" / "<<nentries<<" wrong"<<"\n";

    g->Close();
    f->Close();
}

void checkTTree() {

	tree3AddBranch();

}
