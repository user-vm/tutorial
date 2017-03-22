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
    'DecayTimeResolutionModel':  { 'sigmas': [ 0.020, ], 'fractions': [] },
    'DecayTimeResolutionBias': 0., # if there is a shift
    'DecayTimeResolutionScaleFactor': 1.0, # usually the errors need a bit of scaling

    'AcceptanceFunction': 'Spline',
    'SplineAcceptance': { # configure spline acceptance parameters
        'KnotPositions':    [ 0.5, 1.0, 1.5, 2.0, 3.0, 12.0 ],
        'KnotCoefficients': { # different between generation and fit
            #'GEN': [ 1.96857e-01, 3.46572e-01, 7.22944e-01, 
            #         8.46754e-01, 1.23892e+00, 1.11654e+00 ],
            #'FIT': [ 1.96857e-01, 3.46572e-01, 7.22944e-01, 
            #         8.46754e-01, 1.23892e+00, 1.11654e+00 ],
			'GEN': [ 1.96857e-01, 3.46572e-01, 7.22944e-01, 
                     8.46754e-01, 1.23892e+00, 1.11654e+00 ],
            'FIT': [ 1.96857e-01, 3.46572e-01, 7.22944e-01, 
                     8.46754e-01, 1.23892e+00, 1.11654e+00 ],
			#'GEN': [ 4.5853e-01, 6.8963e-01, 8.8528e-01,
            #         1.1296e+00, 1.2232e+00, 1.2277e+00 ],
            #'FIT': [ 4.5853e-01, 6.8963e-01, 8.8528e-01,
            #         1.1296e+00, 1.2232e+00, 1.2277e+00 ],
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
	'DataFileName': '/mnt/cdrom/data_Bs2Dspipipi_11_final_sweight.root',
	# data set is in a workspace already
	'DataWorkSpaceName':    None,
	# name of data set inside workspace
	'DataSetNames':         'DecayTree',
	# mapping between observables and variable name in data set
	'DataSetVarNameMapping': {
            'time':    'Bs_ct',
            'timeerr': 'Bs_cterr',
            #'eta':     'Bs_TAGOMEGA_OS',
			'eta':     'Bs_SS_nnetKaon_PROB',
            'qf':      'Ds_ID',
			'qt':      'Bs_SS_nnetKaon_DEC',
            #'qt': 	   'Bs_TAGDECISION_OS',
            'weight':  'N_Bs_sw',
	},
	'DataSetCuts':	None,

}

#vim: sw=4:et
