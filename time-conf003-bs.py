{
    'Debug': True,
    'UseKFactor': False,
    'ParameteriseIntegral': False,

    'FitConfig': {
        'Optimize': 1,
        'Offset': True,
        'NumCPU': 1,
        'Strategy': 2,
    },

    'IsData': False,
    'Blinding': True,

    # 40 fs average resolution
    'DecayTimeResolutionModel':  { 'sigmas': [ 0.039, ], 'fractions': [] },
    'DecayTimeResolutionBias': 0., # if there is a shift
    'DecayTimeResolutionScaleFactor': 1.0, # usually the errors need a bit of scaling

    'AcceptanceFunction': 'Spline',
    'SplineAcceptance': { # configure spline acceptance parameters
        'KnotPositions':    [ 0.5, 1.0, 1.5, 2.0, 3.0, 12.0 ],
        'KnotCoefficients': { # different between generation and fit
            'GEN': [ 4.51762e-01, 7.30942e-01, 1.19231,
                     1.34329e+00, 1.60870e+00, 1.55630e+00 ],
            'FIT': [ 4.51762e-01, 7.30942e-01, 1.19231,
                     1.34329e+00, 1.60870e+00, 1.55630e+00 ],
            },
        },
	
    # dummy shape for easy testing in toys:
    #  ^              * zero from omega=0 to omega0
    #  |      *  |    * quadratic rise starting at omega0
    #  |     * * |    * turning point omega_c calculated
    #  |    *   *|      to match desired average omega
    #  |  **     * f  * from there, linear down to point (0.5, f)
    #  ***-------+
    #  0 omega0  0.5
    'TrivialMistagParams': {
        'omegaavg': 0.350, # desired expectation value of mistag distribution
        'omega0': 0.07, # start quadratic increase at omega0
        'f': 0.25, # final point P(0.5) = f
        },

    'MistagCalibParams': { # tagging calibration parameters
        'p0':     0.350, #0.345
        'p1':     1.000, #0.980
        'etaavg': 0.350,
        },
	


    'constParams': [
        '.*_scalefactor', # anything ending in '_scalefactor'...
        'Bs2DsPi_accpetance_SplineAccCoeff[0-9]+', # spline acceptance fixed
        ],

    'NBinsAcceptance': 100,

   
    # file to read from
	'DataFileName': '/home/user/cmtuser/Urania_v5r0/PhysFit/B2DXFitters/Bs2Dspipipi_MC_fullSel_reweighted_combined_NO_SHORT_T.root',
	# data set is in a workspace already
	'DataWorkSpaceName':    None,
	# name of data set inside workspace
	'DataSetNames':         'DecayTree',
	# mapping between observables and variable name in data set
	'DataSetVarNameMapping': {
            'time':    'Bs_ct',
            'timeerr': 'Bs_cterr',
            'etaOS':   'Bs_TAGOMEGA_OS',
            'etaSS1':  'Bs_SS_Kaon_PROB',
			'etaSS2':  'Bs_SS_nnetKaon_PROB',
            'qf':      'Ds_ID',
			'qtSS1':   'corrKQT',
			'qtSS2':   'corrnnetKQT',
            'qtOS':    'Bs_TAGDECISION_OS',
            'weight':  'weight',
	},
	'DataSetCuts':	None,

}

#vim: sw=4:et
