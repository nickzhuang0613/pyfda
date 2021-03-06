# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the PlotImz class
"""
import logging
logger = logging.getLogger(__name__)

import collections
from pyfda.libs.compat import (QCheckBox, QWidget, QComboBox, QLineEdit, QLabel, QTabWidget,
                               QPushButton, QPushButtonRT, QFontMetrics, pyqtSignal, 
                               QEvent, Qt, QHBoxLayout, QVBoxLayout, QGridLayout,
                               QSizePolicy)

import numpy as np
from pyfda.libs.pyfda_lib import to_html, safe_eval
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import (qcmb_box_populate, qget_cmb_box, qset_cmb_box, 
                                     qstyle_widget, QVLine)
from pyfda.libs.pyfda_fft_windows_lib import get_window_names, calc_window_function
from .plot_fft_win import Plot_FFT_win
from pyfda.pyfda_rc import params # FMT string for QLineEdit fields, e.g. '{:.3g}'

class PlotImpz_UI(QWidget):
    """
    Create the UI for the PlotImpz class
    """
    # incoming: not implemented at the moment, update_N is triggered directly
    # by plot_impz
    # sig_rx = pyqtSignal(object)
    # outgoing: from various UI elements to PlotImpz ('ui_changed':'xxx')
    sig_tx = pyqtSignal(object)
    # outgoing to local fft window
    sig_tx_fft = pyqtSignal(object)


    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (FilterCoeffs)
        """
        super(PlotImpz_UI, self).__init__(parent)

        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        self.mSize = QFontMetrics(QPushButton().font()).width("m")
        # row4_height = mSize.lineSpacing() * 4

        # initial settings
        self.N_start = 0
        self.N_user = 0
        self.N = 0

        # time
        self.plt_time_resp = "stem"
        self.plt_time_stim = "line"
        self.plt_time_stmq = "none"
        self.plt_time_spgr = "none"

        self.bottom_t = -80 # initial value for log. scale (time)
        self.nfft_spgr_time = 256 # number of fft points per spectrogram segment
        self.ovlp_spgr_time = 128 # number of overlap points between spectrogram segments
        self.mode_spgr_time = "magnitude"

        # stimuli
        self.cmb_stim_item = "impulse"
        self.cmb_stim_periodic_item = 'square'
        self.stim = "dirac"
        self.impulse_type = 'dirac'
        self.sinusoid_type = 'sine'

        self.chirp_type = 'linear'
        self.modulation_type = 'am'
        self.noise = "None"

        self.f1 = 0.02
        self.f2 = 0.03
        self.A1 = 1.0
        self.A2 = 0.0
        self.phi1 = self.phi2 = 0
        self.T1 = self.T2 = 0
        self.TW1 = self.TW2 = 1
        self.BW1 = self.BW2 = 0.5
        self.noi = 0.1
        self.noise = 'none'
        self.DC = 0.0
        self.stim_formula = "A1 * abs(sin(2 * pi * f1 * n))"
        self.stim_par1 = 0.5

        # frequency
        self.cmb_freq_display_item = "mag"
        self.plt_freq_resp = "line"
        self.plt_freq_stim = "none"
        self.plt_freq_stmq = "none"

        self.bottom_f = -120 # initial value for log. scale
        self.param = None


        # dictionary for fft window settings
        self.win_dict = fb.fil[0]['win_fft']
        self.fft_window = None # handle for FFT window pop-up widget
        self.window_name = "Rectangular"

        self.f_scale = fb.fil[0]['f_S']
        self.t_scale = fb.fil[0]['T_S']

        # dictionaries with widgets needed for the various stimuli
        self.stim_wdg_dict = collections.OrderedDict()
        self.stim_wdg_dict.update(
        {"none":    {"dc", "noise"},
         "dirac":   {"dc", "a1", "T1", "norm", "noise"},
         "sinc":    {"dc", "a1", "a2", "T1", "T2", "f1", "f2", "norm", "noise"},
         "gauss":   {"dc", "a1", "a2", "T1", "T2", "f1", "f2", "BW1", "BW2", "norm", "noise"},
         "rect":    {"dc", "a1", "T1", "TW1", "norm", "noise"},
         "step":    {"a1", "T1", "noise"},
         "cos":     {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
         "sine":    {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
         "exp":     {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
         "diric":   {"dc", "a1", "phi1", "T1", "TW1", "f1", "noise"},

         "chirp":   {"dc", "a1", "phi1", "f1", "f2", "noise"},
         "triang":  {"dc", "a1", "phi1", "f1", "noise", "bl"},
         "saw":     {"dc", "a1", "phi1", "f1", "noise", "bl"},
         "square":  {"dc", "a1", "phi1", "f1", "noise", "bl", "par1"},
         "comb":    {"dc", "a1", "phi1", "f1", "noise"},
         "am":      {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
         "pmfm":    {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
         "formula": {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "BW1", "BW2", "noise"}
         })
        # data / text / tooltip for stimulus type combobox. First element is combobox tooltip.
        self.plot_styles_list =\
                [("Plot style"),
                 ("none","None",""),
                 ("dots","Dots",""),
                 ("line","Line",""),
                 ("line*","Line*",""),
                 ("stem","Stem",""),
                 ("stem*","Stem*",""),
                 ("step","Step",""),
                 ("step*","Step*","")
                 ]
        self.cmb_stim_items =\
                [("<span>Stimulus category.</span>"),
                 ("none", "None", "<span>Only noise and DC can be selected.</span>"),
                 ("impulse", "Impulse", "<span>Different impulses</span>"),
                 ("step", "Step", "<span>Calculate step response and its error.</span>"),
                 ("sinusoid", "Sinusoid", "<span>Sinusoidal waveforms</span>"),
                 ("chirp", "Chirp", "<span>Different frequency sweeps.</span>"),
                 ("periodic", "Periodic", "<span>Periodic functions with discontinuities, "
                                          "band-limited or with aliasing.</span>"),
                 ("modulation", "Modulat.", "<span>Modulated waveforms.</span>"),
                 ("formula", "Formula", "<span>Formula defined stimulus.</span>")
                ]

        # data / text / tooltip for periodic signals' combobox. 
        self.cmb_stim_periodic_items =\
                ["<span>Periodic functions with discontinuities.</span>",
                 ("square","Square", "<span>Square signal with duty cycle &alpha;.</span>"),
                 ("saw","Saw", "Sawtooth signal."),
                 ("triang", "Triang","Triangular signal."), 
                 ("comb", "Comb","Comb signal.")
                ]

        # data / text / tooltip for chirp signals' combobox.
        self.cmb_stim_chirp_items =\
                [ "<span>Type of frequency sweep from <i>f</i><sub>1</sub> to "
                  "<i>f</i><sub>1</sub></span>",
                 ("linear", "Lin", "Linear frequency sweep"),
                 ("quadratic", "Square","Quadratic frequency sweep"),
                 ("logarithmic", "Log", "Logarithmic frequency sweep"),
                 ("hyperbolic", "Hyper",  "Hyperbolic frequency sweep")
                ]

        self.cmb_stim_impulse_items=\
                [ "<span>Different aperiodic impulse forms</span>",
                 ("dirac","Dirac","<span>Discrete-time dirac impulse for simulating "
                                  "impulse and frequency response.</span>"),
                 ("gauss","Gauss", "<span>Gaussian pulse with bandpass spectrum and "
                                   "controllable relative -6 dB bandwidth.</span>"),
                 ("sinc", "Sinc", "<span>Sinc pulse with rectangular baseband spectrum</span>"),
                 ("rect", "Rect", "<span>Rectangular pulse with sinc-shaped spectrum</span>")
                ]

        self.cmb_stim_sinusoid_items=\
                ["Sinusoidal or similar signals",
                 ("sine","Sine", "Sine signal"),
                 ("cos","Cos", "Cosine signal"),
                 ("exp", "Exp", "Complex exponential"),
                 ("diric", "Sinc", "<span>Periodic Sinc (Dirichlet function)</span>")
                ]

        self.cmb_time_spgr_items=\
                ["<span>Show Spectrogram for selected signal.</span>",
                 ("none","None",""),
                 ("xn","x[n]",""),
                 ("xqn","x_q[n]",""),
                 ("yn","y[n]","")
                 ]

        # data / text / tooltip for noise stimulus combobox.
        self.cmb_stim_noise_items =\
                [ "Type of additive noise.",
                 ("none", "None", ""),
                 ("gauss", "Gauss", "<span>Normal- or Gauss-distributed process with "
                                    "std. deviation &sigma;.</span>"),
                 ("uniform", "Uniform", "<span>Uniformly distributed process in the "
                                        "range &plusmn; &Delta;/2.</span>"),
                 ("prbs", "PRBS", "<span>Pseudo-Random Binary Sequence with values "
                                      "&plusmn; A.</span>"),
                 ("mls", "MLS", "<span>Maximum Length Sequence with values &plusmn; A. "
                                 "The sequence is always the same as the state is not "
                                 "stored for the next sequence start.</span>"),
                 ("brownian", "Brownian", "<span>Brownian (cumulated sum) process based "
                                      " on Gaussian noise with std. deviation &sigma;.</span>")
                 ]

        # data / text / tooltip for spectrum display combobox.                
        self.cmb_freq_display_items =\
                ["<span>Select how to display the spectrum.</span>",
                 ("mag","Magnitude", "<span>Spectral magnitude</span>"),
                 ("mag_phi","Mag. / Phase", "<span>Magnitude and phase.</span>"),
                 ("re_im", "Re. / Imag.","<span>Real and imaginary part of spectrum.</span>")
                ]

        self._construct_UI()
        self._enable_stim_widgets()
        self.update_N(emit=False) # also updates window function
        self._update_noi()


    def _construct_UI(self):
        # ----------- ---------------------------------------------------
        # Run control widgets
        # ---------------------------------------------------------------
        self.chk_auto_run = QCheckBox("Auto", self)
        self.chk_auto_run.setObjectName("chk_auto_run")
        self.chk_auto_run.setToolTip("<span>Update response automatically when "
                                     "parameters have been changed.</span>")
        self.chk_auto_run.setChecked(True)

        self.but_run = QPushButton(self)
        self.but_run.setText("RUN")
        self.but_run.setToolTip("Run simulation")
        self.but_run.setEnabled(not self.chk_auto_run.isChecked())

        self.cmb_sim_select = QComboBox(self)
        self.cmb_sim_select.addItems(["Float","Fixpoint"])
        qset_cmb_box(self.cmb_sim_select, "Float")
        self.cmb_sim_select.setToolTip("<span>Simulate floating-point or fixpoint response."
                                 "</span>")

        self.lbl_N_points = QLabel(to_html("N", frmt='bi')  + " =", self)
        self.led_N_points = QLineEdit(self)
        self.led_N_points.setText(str(self.N))
        self.led_N_points.setToolTip("<span>Number of displayed data points. "
                                   "<i>N</i> = 0 tries to choose for you.</span>")

        self.lbl_N_start = QLabel(to_html("N_0", frmt='bi') + " =", self)
        self.led_N_start = QLineEdit(self)
        self.led_N_start.setText(str(self.N_start))
        self.led_N_start.setToolTip("<span>First point to plot.</span>")

        #self.chk_fx_scale = QCheckBox("Int. scale", self)
        self.chk_fx_scale = QPushButton("FX Int")
        self.chk_fx_scale.setObjectName("chk_fx_scale")
        self.chk_fx_scale.setToolTip("<span>Display data with integer (fixpoint) scale.</span>")
        self.chk_fx_scale.setCheckable(True)
        self.chk_fx_scale.setChecked(False)

        self.chk_stim_options = QPushButton("Stimuli")
        self.chk_stim_options.setObjectName("chk_stim_options")
        self.chk_stim_options.setToolTip("<span>Show stimulus options.</span>")
        self.chk_stim_options.setCheckable(True)
        self.chk_stim_options.setChecked(True)

        self.lbl_stim_cmplx_warn = QLabel(self)
        self.lbl_stim_cmplx_warn = QLabel(to_html("Cmplx!", frmt='b'), self)
        self.lbl_stim_cmplx_warn.setToolTip('<span>Signal is complex valued, '
                                    'single-sided and H<sub>id</sub> spectra may be wrong.</span>')
        self.lbl_stim_cmplx_warn.setStyleSheet("background-color : yellow;"
                                               "border : 1px solid grey")

        self.but_fft_win = QPushButton(self)
        self.but_fft_win.setText("WIN FFT")
        self.but_fft_win.setToolTip('<span> time and frequency response of FFT Window '
                                    '(can be modified in the "Frequency" tab)</span>')
        self.but_fft_win.setCheckable(True)
        self.but_fft_win.setChecked(False)

        layH_ctrl_run = QHBoxLayout()
        layH_ctrl_run.addWidget(self.but_run)
        #layH_ctrl_run.addWidget(self.lbl_sim_select)
        layH_ctrl_run.addWidget(self.cmb_sim_select)
        layH_ctrl_run.addWidget(self.chk_auto_run)
        layH_ctrl_run.addWidget(self.lbl_N_start)
        layH_ctrl_run.addWidget(self.led_N_start)
        layH_ctrl_run.addWidget(self.lbl_N_points)
        layH_ctrl_run.addWidget(self.led_N_points)
        layH_ctrl_run.addStretch(2)
        layH_ctrl_run.addWidget(self.chk_fx_scale)
        layH_ctrl_run.addStretch(2)
        #layH_ctrl_run.addWidget(lbl_stim_options)
        layH_ctrl_run.addWidget(self.chk_stim_options)
        layH_ctrl_run.addStretch(2)
        layH_ctrl_run.addWidget(self.lbl_stim_cmplx_warn)
        layH_ctrl_run.addStretch(2)
        layH_ctrl_run.addWidget(self.but_fft_win)
        layH_ctrl_run.addStretch(10)

        #layH_ctrl_run.setContentsMargins(*params['wdg_margins'])

        self.wdg_ctrl_run = QWidget(self)
        self.wdg_ctrl_run.setLayout(layH_ctrl_run)
        # --- end of run control ----------------------------------------

        # ----------- ---------------------------------------------------
        # Controls for time domain
        # ---------------------------------------------------------------
        self.lbl_plt_time_stim = QLabel(to_html("Stimulus x", frmt='bi'), self)
        self.cmb_plt_time_stim = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_time_stim, self.plot_styles_list, self.plt_time_stim)
        self.cmb_plt_time_stim.setToolTip("<span>Plot style for stimulus.</span>")

        self.lbl_plt_time_stmq = QLabel(to_html("&nbsp;&nbsp;Fixp. Stim. x_Q", frmt='bi'), self)
        self.cmb_plt_time_stmq = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_time_stmq, self.plot_styles_list, self.plt_time_stmq)
        self.cmb_plt_time_stmq.setToolTip("<span>Plot style for <em>fixpoint</em> "
                                          "(quantized) stimulus.</span>")

        lbl_plt_time_resp = QLabel(to_html("&nbsp;&nbsp;Response y", frmt='bi'), self)
        self.cmb_plt_time_resp = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_time_resp, self.plot_styles_list, self.plt_time_resp)
        self.cmb_plt_time_resp.setToolTip("<span>Plot style for response.</span>")

        self.chk_win_time = QPushButton("FFT Window")
        self.chk_win_time.resize(self.chk_win_time.sizeHint().width(), 
                                 self.chk_win_time.sizeHint().height())
        self.chk_win_time.setObjectName("chk_win_time")
        self.chk_win_time.setToolTip('<span>Show FFT windowing function (can be '
                                     'modified in the "Frequency" tab).</span>')
        self.chk_win_time.setCheckable(True)
        self.chk_win_time.setChecked(False)
        
        line1 = QVLine()
        line2 = QVLine(width=5)
        
        self.chk_log_time = QPushButton("dB")
        self.chk_log_time.setMaximumWidth(self.mSize * 4)
        self.chk_log_time.setObjectName("chk_log_time")
        self.chk_log_time.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chk_log_time.setCheckable(True)
        self.chk_log_time.setChecked(False)

        self.lbl_log_bottom_time = QLabel(to_html("min =", frmt='bi'), self)
        self.lbl_log_bottom_time.setVisible(True)
        self.led_log_bottom_time = QLineEdit(self)
        self.led_log_bottom_time.setText(str(self.bottom_t))
        self.led_log_bottom_time.setToolTip("<span>Minimum display value for time "
                                            "and spectrogram plots with log. scale.</span>")
        self.led_log_bottom_time.setVisible(True)

        lbl_plt_time_spgr = QLabel(to_html("&nbsp;&nbsp;Spectrogram", frmt='bi'), self)
        self.cmb_plt_time_spgr = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_time_spgr, self.cmb_time_spgr_items, self.plt_time_spgr)
        spgr_en = self.plt_time_spgr != "none"

        self.chk_log_spgr_time = QPushButton("dB")
        self.chk_log_spgr_time.setMaximumWidth(self.mSize * 4)
        self.chk_log_spgr_time.setObjectName("chk_log_spgr")
        self.chk_log_spgr_time.setToolTip("<span>Logarithmic scale for spectrogram.</span>")
        self.chk_log_spgr_time.setCheckable(True)
        self.chk_log_spgr_time.setChecked(True)
        self.chk_log_spgr_time.setVisible(spgr_en)

        self.lbl_nfft_spgr_time = QLabel(to_html("&nbsp;N_FFT =", frmt='bi'), self)
        self.lbl_nfft_spgr_time.setVisible(spgr_en)
        self.led_nfft_spgr_time = QLineEdit(self)
        self.led_nfft_spgr_time.setText(str(self.nfft_spgr_time))
        self.led_nfft_spgr_time.setToolTip("<span>Number of FFT points per "
                                           "spectrogram segment.</span>")
        self.led_nfft_spgr_time.setVisible(spgr_en)

        self.lbl_ovlp_spgr_time = QLabel(to_html("&nbsp;N_OVLP =", frmt='bi'), self)
        self.lbl_ovlp_spgr_time.setVisible(spgr_en)
        self.led_ovlp_spgr_time = QLineEdit(self)
        self.led_ovlp_spgr_time.setText(str(self.ovlp_spgr_time))
        self.led_ovlp_spgr_time.setToolTip("<span>Number of overlap data points "
                                           "between spectrogram segments.</span>")
        self.led_ovlp_spgr_time.setVisible(spgr_en)

        self.lbl_mode_spgr_time = QLabel(to_html("&nbsp;Mode", frmt='bi'), self)
        self.lbl_mode_spgr_time.setVisible(spgr_en)
        self.cmb_mode_spgr_time = QComboBox(self)
        spgr_modes = [("PSD","psd"), ("Mag.","magnitude"),\
                      ("Angle","angle"), ("Phase","phase")]
        for i in spgr_modes:
            self.cmb_mode_spgr_time.addItem(*i)
        qset_cmb_box(self.cmb_mode_spgr_time, self.mode_spgr_time, data=True)
        self.cmb_mode_spgr_time.setToolTip("<span>Spectrogram display mode.</span>")
        self.cmb_mode_spgr_time.setVisible(spgr_en)

        self.lbl_byfs_spgr_time = QLabel(to_html("&nbsp;per f_S", frmt='b'), self)
        self.lbl_byfs_spgr_time.setVisible(spgr_en)
        self.chk_byfs_spgr_time = QCheckBox(self)
        self.chk_byfs_spgr_time.setObjectName("chk_log_spgr")
        self.chk_byfs_spgr_time.setToolTip("<span>Display spectral density i.e. "
                                           "scale by f_S</span>")
        self.chk_byfs_spgr_time.setChecked(True)
        self.chk_byfs_spgr_time.setVisible(spgr_en)


        # self.lbl_colorbar_time = QLabel(to_html("&nbsp;Col.bar", frmt='b'), self)
        # self.lbl_colorbar_time.setVisible(spgr_en)
        # self.chk_colorbar_time = QCheckBox(self)
        # self.chk_colorbar_time.setObjectName("chk_colorbar_time")
        # self.chk_colorbar_time.setToolTip("<span>Enable colorbar</span>")
        # self.chk_colorbar_time.setChecked(True)
        # self.chk_colorbar_time.setVisible(spgr_en)

        self.chk_fx_limits = QCheckBox("Min/max.", self)
        self.chk_fx_limits.setObjectName("chk_fx_limits")
        self.chk_fx_limits.setToolTip("<span>Display limits of fixpoint range.</span>")
        self.chk_fx_limits.setChecked(False)

        layH_ctrl_time = QHBoxLayout()
        layH_ctrl_time.addWidget(self.lbl_plt_time_stim)
        layH_ctrl_time.addWidget(self.cmb_plt_time_stim)
        #
        layH_ctrl_time.addWidget(self.lbl_plt_time_stmq)
        layH_ctrl_time.addWidget(self.cmb_plt_time_stmq)
        #
        layH_ctrl_time.addWidget(lbl_plt_time_resp)
        layH_ctrl_time.addWidget(self.cmb_plt_time_resp)
        #
        layH_ctrl_time.addWidget(self.chk_win_time)
        layH_ctrl_time.addSpacing(5)
        layH_ctrl_time.addWidget(line1)
        layH_ctrl_time.addSpacing(5)
        #layH_ctrl_time.addStretch(1)
        #layH_ctrl_time.addWidget(line2)
        layH_ctrl_time.addWidget(self.chk_log_time)
        layH_ctrl_time.addWidget(self.lbl_log_bottom_time)
        layH_ctrl_time.addWidget(self.led_log_bottom_time)
        #
        layH_ctrl_time.addStretch(1)
        #
        layH_ctrl_time.addWidget(lbl_plt_time_spgr)
        layH_ctrl_time.addWidget(self.cmb_plt_time_spgr)
        layH_ctrl_time.addWidget(self.chk_log_spgr_time)
        layH_ctrl_time.addWidget(self.lbl_nfft_spgr_time)
        layH_ctrl_time.addWidget(self.led_nfft_spgr_time)
        layH_ctrl_time.addWidget(self.lbl_ovlp_spgr_time)
        layH_ctrl_time.addWidget(self.led_ovlp_spgr_time)
        layH_ctrl_time.addWidget(self.lbl_mode_spgr_time)
        layH_ctrl_time.addWidget(self.cmb_mode_spgr_time)
        layH_ctrl_time.addWidget(self.lbl_byfs_spgr_time)
        layH_ctrl_time.addWidget(self.chk_byfs_spgr_time)

        layH_ctrl_time.addStretch(2)
        layH_ctrl_time.addWidget(self.chk_fx_limits)
        layH_ctrl_time.addStretch(10)

        #layH_ctrl_time.setContentsMargins(*params['wdg_margins'])

        self.wdg_ctrl_time = QWidget(self)
        self.wdg_ctrl_time.setLayout(layH_ctrl_time)
        # ---- end time domain ------------------

        # ---------------------------------------------------------------
        # Controls for frequency domain
        # ---------------------------------------------------------------
        self.lbl_plt_freq_stim = QLabel(to_html("Stimulus X", frmt='bi'), self)
        self.cmb_plt_freq_stim = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_freq_stim, self.plot_styles_list, self.plt_freq_stim)
        #self.cmb_plt_freq_stim.setToolTip("<span>Plot style for stimulus.</span>")

        self.lbl_plt_freq_stmq = QLabel(to_html("&nbsp;Fixp. Stim. X_Q", frmt='bi'), self)
        self.cmb_plt_freq_stmq = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_freq_stmq, self.plot_styles_list, self.plt_freq_stmq)
        self.cmb_plt_freq_stmq.setToolTip("<span>Plot style for <em>fixpoint</em> "
                                          "(quantized) stimulus.</span>")

        lbl_plt_freq_resp = QLabel(to_html("&nbsp;Response Y", frmt='bi'), self)
        self.cmb_plt_freq_resp = QComboBox(self)
        qcmb_box_populate(self.cmb_plt_freq_resp, self.plot_styles_list, self.plt_freq_resp)
        self.cmb_plt_freq_resp.setToolTip("<span>Plot style for response.</span>")

        self.chk_log_freq = QPushButton("dB")
        self.chk_log_freq.setMaximumWidth(self.mSize * 4)
        self.chk_log_freq.setObjectName("chk_log_freq")
        self.chk_log_freq.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chk_log_freq.setCheckable(True)
        self.chk_log_freq.setChecked(True)

        self.lbl_log_bottom_freq = QLabel(to_html("min =", frmt='bi'), self)
        self.lbl_log_bottom_freq.setVisible(self.chk_log_freq.isChecked())
        self.led_log_bottom_freq = QLineEdit(self)
        self.led_log_bottom_freq.setText(str(self.bottom_f))
        self.led_log_bottom_freq.setToolTip("<span>Minimum display value for log. scale.</span>")
        self.led_log_bottom_freq.setVisible(self.chk_log_freq.isChecked())

        if not self.chk_log_freq.isChecked():
            self.bottom_f = 0

        self.cmb_freq_display = QComboBox(self)
        qcmb_box_populate(self.cmb_freq_display, self.cmb_freq_display_items,
                          self.cmb_freq_display_item)
        self.cmb_freq_display.setObjectName("cmb_re_im_freq")

        self.lbl_win_fft = QLabel(to_html("Window", frmt='bi'), self)
        self.cmb_win_fft = QComboBox(self)
        self.cmb_win_fft.addItems(get_window_names())
        self.cmb_win_fft.setToolTip("FFT window type.")
        qset_cmb_box(self.cmb_win_fft, self.window_name)

        self.cmb_win_fft_variant = QComboBox(self)
        self.cmb_win_fft_variant.setToolTip("FFT window variant.")
        self.cmb_win_fft_variant.setVisible(False)

        self.lblWinPar1 = QLabel("Param1")
        self.ledWinPar1 = QLineEdit(self)
        self.ledWinPar1.setText("1")
        self.ledWinPar1.setObjectName("ledWinPar1")

        self.lblWinPar2 = QLabel("Param2")
        self.ledWinPar2 = QLineEdit(self)
        self.ledWinPar2.setText("2")
        self.ledWinPar2.setObjectName("ledWinPar2")

        self.chk_Hf = QPushButtonRT(self, to_html("H_id", frmt="bi"))
        self.chk_Hf.setObjectName("chk_Hf")
        self.chk_Hf.setToolTip("<span>Show ideal frequency response, calculated "
                               "from the filter coefficients.</span>")
        self.chk_Hf.setChecked(False)
        self.chk_Hf.setCheckable(True)

        self.chk_show_info_freq = QPushButtonRT(text=to_html("Info", frmt="b"), margin=20)
        self.chk_show_info_freq.setObjectName("chk_show_info_freq")
        self.chk_show_info_freq.setToolTip("<span>Show infos about signal power "
                                           "and window properties.</span>")
        self.chk_show_info_freq.setCheckable(True)
        self.chk_show_info_freq.setChecked(False)

        layH_ctrl_freq = QHBoxLayout()
        layH_ctrl_freq.addWidget(self.lbl_plt_freq_stim)
        layH_ctrl_freq.addWidget(self.cmb_plt_freq_stim)
        #
        layH_ctrl_freq.addWidget(self.lbl_plt_freq_stmq)
        layH_ctrl_freq.addWidget(self.cmb_plt_freq_stmq)
        #
        layH_ctrl_freq.addWidget(lbl_plt_freq_resp)
        layH_ctrl_freq.addWidget(self.cmb_plt_freq_resp)
        #
        layH_ctrl_freq.addSpacing(5)
        layH_ctrl_freq.addWidget(self.chk_Hf)
        layH_ctrl_freq.addStretch(1)
        layH_ctrl_freq.addWidget(self.chk_log_freq)
        layH_ctrl_freq.addWidget(self.lbl_log_bottom_freq)
        layH_ctrl_freq.addWidget(self.led_log_bottom_freq)
        layH_ctrl_freq.addStretch(1)
        layH_ctrl_freq.addWidget(self.cmb_freq_display)
        layH_ctrl_freq.addStretch(2)
        layH_ctrl_freq.addWidget(self.lbl_win_fft)
        layH_ctrl_freq.addWidget(self.cmb_win_fft)
        layH_ctrl_freq.addWidget(self.cmb_win_fft_variant)
        layH_ctrl_freq.addWidget(self.lblWinPar1)
        layH_ctrl_freq.addWidget(self.ledWinPar1)
        layH_ctrl_freq.addWidget(self.lblWinPar2)
        layH_ctrl_freq.addWidget(self.ledWinPar2)
        layH_ctrl_freq.addStretch(1)
        #layH_ctrl_freq.addWidget(lbl_show_info_freq)
        layH_ctrl_freq.addWidget(self.chk_show_info_freq)
        layH_ctrl_freq.addStretch(10)

        #layH_ctrl_freq.setContentsMargins(*params['wdg_margins'])

        self.wdg_ctrl_freq = QWidget(self)
        self.wdg_ctrl_freq.setLayout(layH_ctrl_freq)
        # ---- end Frequency Domain ------------------

        # =====================================================================
        # Controls for stimuli
        # =====================================================================
        # Create combo box with stimulus categories
        self.lblStimulus = QLabel(to_html("Stimulus", frmt='bi'), self)
        self.cmbStimulus = QComboBox(self)
        qcmb_box_populate(self.cmbStimulus, self.cmb_stim_items, self.cmb_stim_item)

        self.lblStimPar1 = QLabel(to_html("&alpha; =", frmt='b'), self)
        self.ledStimPar1 = QLineEdit(self)
        self.ledStimPar1.setText("0.5")
        self.ledStimPar1.setToolTip("Duty Cycle, 0 ... 1")
        self.ledStimPar1.setObjectName("ledStimPar1")

        self.chk_stim_bl = QPushButton(self)
        self.chk_stim_bl.setText("BL")
        self.chk_stim_bl.setToolTip("<span>Bandlimit the signal to the Nyquist "
                            "frequency to avoid aliasing. However, this is much slower "
                            "to calculate especially for a large number of points.</span>")
        self.chk_stim_bl.setMaximumWidth(self.mSize * 4)
        self.chk_stim_bl.setCheckable(True)
        self.chk_stim_bl.setChecked(True)
        self.chk_stim_bl.setObjectName("stim_bl")

        #-------------------------------------
        self.cmbChirpType = QComboBox(self)
        qcmb_box_populate(self.cmbChirpType, self.cmb_stim_chirp_items, self.chirp_type)

        self.cmbImpulseType = QComboBox(self)
        qcmb_box_populate(self.cmbImpulseType, self.cmb_stim_impulse_items, self.impulse_type)
        
        self.cmbSinusoidType = QComboBox(self)
        qcmb_box_populate(self.cmbSinusoidType, self.cmb_stim_sinusoid_items, self.sinusoid_type)

        self.cmbPeriodicType = QComboBox(self)
        qcmb_box_populate(self.cmbPeriodicType, self.cmb_stim_periodic_items, 
                          self.cmb_stim_periodic_item)

        self.cmbModulationType = QComboBox(self)
        for t in [("AM", "am"), ("PM / FM", "pmfm")]: # text, data
            self.cmbModulationType.addItem(*t)
        qset_cmb_box(self.cmbModulationType, self.modulation_type, data=True)


        #-------------------------------------
        self.chk_norm_impz_f = QCheckBox("Norm", self)
        self.chk_norm_impz_f.setToolTip("<span>Normalize the FFT of the stimulus "
                            "impulse with <i>N<sub>FFT</sub></i> to achieve "
                            "|<i>X(f)</i>| &le; 1. For the dirac pulse, yielding "
                            "|<i>Y(f)</i>|= |<i>H(f)</i>|. DC and Noise need to be "
                            "turned off.</span>")
        self.chk_norm_impz_f.setChecked(True)
        self.chk_norm_impz_f.setObjectName("scale_impz_f")

        self.chk_step_err = QPushButton("Error", self)
        self.chk_step_err.setToolTip("<span>Display the step response error.</span>")
        self.chk_step_err.setMaximumWidth(7*self.mSize)
        self.chk_step_err.setCheckable(True)
        self.chk_step_err.setChecked(False)
        self.chk_step_err.setObjectName("stim_step_err")


        self.lblDC = QLabel(to_html("DC =", frmt='bi'), self)
        self.ledDC = QLineEdit(self)
        self.ledDC.setText(str(self.DC))
        self.ledDC.setToolTip("DC Level")
        self.ledDC.setObjectName("stimDC")

        layHCmbStim = QHBoxLayout()
        layHCmbStim.addWidget(self.cmbStimulus)
        layHCmbStim.addWidget(self.cmbImpulseType)
        layHCmbStim.addWidget(self.cmbSinusoidType)
        layHCmbStim.addWidget(self.cmbChirpType)
        layHCmbStim.addWidget(self.cmbPeriodicType)
        layHCmbStim.addWidget(self.cmbModulationType)
        layHCmbStim.addWidget(self.chk_stim_bl)
        layHCmbStim.addWidget(self.lblStimPar1)
        layHCmbStim.addWidget(self.ledStimPar1)

        layHCmbStim.addWidget(self.chk_norm_impz_f)
        layHCmbStim.addWidget(self.chk_step_err)
        #======================================================================
        self.lblAmp1 = QLabel(to_html("&nbsp;A_1", frmt='bi') + " =", self)
        self.ledAmp1 = QLineEdit(self)
        self.ledAmp1.setText(str(self.A1))
        self.ledAmp1.setToolTip("Stimulus amplitude, complex values like 3j - 1 are allowed")
        self.ledAmp1.setObjectName("stimAmp1")

        self.lblAmp2 = QLabel(to_html("&nbsp;A_2", frmt='bi') + " =", self)
        self.ledAmp2 = QLineEdit(self)
        self.ledAmp2.setText(str(self.A2))
        self.ledAmp2.setToolTip("Stimulus amplitude 2, complex values like 3j - 1 are allowed")
        self.ledAmp2.setObjectName("stimAmp2")

        #----------------------------------------------
        self.lblPhi1 = QLabel(to_html("&nbsp;&phi;_1", frmt='bi') + " =", self)
        self.ledPhi1 = QLineEdit(self)
        self.ledPhi1.setText(str(self.phi1))
        self.ledPhi1.setToolTip("Stimulus phase")
        self.ledPhi1.setObjectName("stimPhi1")
        self.lblPhU1 = QLabel(to_html("&deg;", frmt='b'), self)

        self.lblPhi2 = QLabel(to_html("&nbsp;&phi;_2", frmt='bi') + " =", self)
        self.ledPhi2 = QLineEdit(self)
        self.ledPhi2.setText(str(self.phi2))
        self.ledPhi2.setToolTip("Stimulus phase 2")
        self.ledPhi2.setObjectName("stimPhi2")
        self.lblPhU2 = QLabel(to_html("&deg;", frmt='b'), self)

        #----------------------------------------------
        self.lbl_T1 = QLabel(to_html("&nbsp;T_1", frmt='bi') + " =", self)
        self.led_T1 = QLineEdit(self)
        self.led_T1.setText(str(self.T1))
        self.led_T1.setToolTip("Time shift")
        self.led_T1.setObjectName("stimT1")
        self.lbl_TU1 = QLabel(to_html("T_S", frmt='b'), self)

        self.lbl_T2 = QLabel(to_html("&nbsp;T_2", frmt='bi') + " =", self)
        self.led_T2 = QLineEdit(self)
        self.led_T2.setText(str(self.T2))
        self.led_T2.setToolTip("Time shift 2")
        self.led_T2.setObjectName("stimT2")
        self.lbl_TU2 = QLabel(to_html("T_S", frmt='b'), self)
        
        #----------------------------------------------
        self.lbl_TW1 = QLabel(to_html("&nbsp;&Delta;T_1", frmt='bi') + " =", self)
        self.led_TW1 = QLineEdit(self)
        self.led_TW1.setText(str(self.TW1))
        self.led_TW1.setToolTip("Time width")
        self.led_TW1.setObjectName("stimTW1")
        self.lbl_TWU1 = QLabel(to_html("T_S", frmt='b'), self)

        self.lbl_TW2 = QLabel(to_html("&nbsp;&Delta;T_2", frmt='bi') + " =", self)
        self.led_TW2 = QLineEdit(self)
        self.led_TW2.setText(str(self.TW2))
        self.led_TW2.setToolTip("Time width 2")
        self.led_TW2.setObjectName("stimTW2")
        self.lbl_TWU2 = QLabel(to_html("T_S", frmt='b'), self)

        #----------------------------------------------
        self.txtFreq1_f = to_html("&nbsp;f_1", frmt='bi') + " ="
        self.txtFreq1_k = to_html("&nbsp;k_1", frmt='bi') + " ="
        self.lblFreq1 = QLabel(self.txtFreq1_f, self)
        self.ledFreq1 = QLineEdit(self)
        self.ledFreq1.setText(str(self.f1))
        self.ledFreq1.setToolTip("Stimulus frequency")
        self.ledFreq1.setObjectName("stimFreq1")
        self.lblFreqUnit1 = QLabel("f_S", self)

        self.txtFreq2_f = to_html("&nbsp;f_2", frmt='bi') + " ="
        self.txtFreq2_k = to_html("&nbsp;k_2", frmt='bi') + " ="
        self.lblFreq2 = QLabel(self.txtFreq2_f, self)
        self.ledFreq2 = QLineEdit(self)
        self.ledFreq2.setText(str(self.f2))
        self.ledFreq2.setToolTip("Stimulus frequency 2")
        self.ledFreq2.setObjectName("stimFreq2")
        self.lblFreqUnit2 = QLabel("f_S", self)
        
        #----------------------------------------------
        self.lbl_BW1 = QLabel(to_html(self.tr("&nbsp;BW_1"), frmt='bi') + " =", self)
        self.led_BW1 = QLineEdit(self)
        self.led_BW1.setText(str(self.BW1))
        self.led_BW1.setToolTip(self.tr("Relative bandwidth"))
        self.led_BW1.setObjectName("stimBW1")

        self.lbl_BW2 = QLabel(to_html(self.tr("&nbsp;BW_2"), frmt='bi') + " =", self)
        self.led_BW2 = QLineEdit(self)
        self.led_BW2.setText(str(self.BW2))
        self.led_BW2.setToolTip(self.tr("Relative bandwidth 2"))
        self.led_BW2.setObjectName("stimBW2")

        #----------------------------------------------
        self.lblNoise = QLabel(to_html("&nbsp;Noise", frmt='bi'), self)
        self.cmbNoise = QComboBox(self)
        qcmb_box_populate(self.cmbNoise, self.cmb_stim_noise_items, self.noise)

        self.lblNoi = QLabel("not initialized", self)
        self.ledNoi = QLineEdit(self)
        self.ledNoi.setText(str(self.noi))
        self.ledNoi.setToolTip("not initialized")
        self.ledNoi.setObjectName("stimNoi")

        layGStim = QGridLayout()

        layGStim.addWidget(self.lblStimulus, 0, 0)
        layGStim.addWidget(self.lblDC, 1, 0)

        layGStim.addLayout(layHCmbStim, 0, 1)
        layGStim.addWidget(self.ledDC,  1, 1)

        layGStim.addWidget(self.lblAmp1, 0, 2)
        layGStim.addWidget(self.lblAmp2, 1, 2)

        layGStim.addWidget(self.ledAmp1, 0, 3)
        layGStim.addWidget(self.ledAmp2, 1, 3)

        layGStim.addWidget(self.lblPhi1, 0, 4)
        layGStim.addWidget(self.lblPhi2, 1, 4)

        layGStim.addWidget(self.ledPhi1, 0, 5)
        layGStim.addWidget(self.ledPhi2, 1, 5)

        layGStim.addWidget(self.lblPhU1, 0, 6)
        layGStim.addWidget(self.lblPhU2, 1, 6)

        layGStim.addWidget(self.lbl_T1, 0, 7)
        layGStim.addWidget(self.lbl_T2, 1, 7)

        layGStim.addWidget(self.led_T1, 0, 8)
        layGStim.addWidget(self.led_T2, 1, 8)

        layGStim.addWidget(self.lbl_TU1, 0, 9)
        layGStim.addWidget(self.lbl_TU2, 1, 9)

        layGStim.addWidget(self.lbl_TW1, 0, 10)
        layGStim.addWidget(self.lbl_TW2, 1, 10)

        layGStim.addWidget(self.led_TW1, 0, 11)
        layGStim.addWidget(self.led_TW2, 1, 11)

        layGStim.addWidget(self.lbl_TWU1, 0, 12)
        layGStim.addWidget(self.lbl_TWU2, 1, 12)

        layGStim.addWidget(self.lblFreq1, 0, 13)
        layGStim.addWidget(self.lblFreq2, 1, 13)

        layGStim.addWidget(self.ledFreq1, 0, 14)
        layGStim.addWidget(self.ledFreq2, 1, 14)

        layGStim.addWidget(self.lblFreqUnit1, 0, 15)
        layGStim.addWidget(self.lblFreqUnit2, 1, 15)
        
        layGStim.addWidget(self.lbl_BW1, 0, 16)
        layGStim.addWidget(self.lbl_BW2, 1, 16)

        layGStim.addWidget(self.led_BW1, 0, 17)
        layGStim.addWidget(self.led_BW2, 1, 17)


        layGStim.addWidget(self.lblNoise, 0, 18)
        layGStim.addWidget(self.lblNoi, 1, 18)

        layGStim.addWidget(self.cmbNoise, 0, 19)
        layGStim.addWidget(self.ledNoi, 1, 19)

        #----------------------------------------------
        self.lblStimFormula = QLabel(to_html("x =", frmt='bi'), self)
        self.ledStimFormula = QLineEdit(self)
        self.ledStimFormula.setText(str(self.stim_formula))
        self.ledStimFormula.setToolTip("<span>Enter formula for stimulus in numexpr syntax."
                                  "</span>")
        self.ledStimFormula.setObjectName("stimFormula")

        layH_ctrl_stim_formula = QHBoxLayout()
        layH_ctrl_stim_formula.addWidget(self.lblStimFormula)
        layH_ctrl_stim_formula.addWidget(self.ledStimFormula,10)

        #----------------------------------------------
        #layG_ctrl_stim = QGridLayout()
        layH_ctrl_stim_par = QHBoxLayout()

        layH_ctrl_stim_par.addLayout(layGStim)

        layV_ctrl_stim = QVBoxLayout()
        layV_ctrl_stim.addLayout(layH_ctrl_stim_par)
        layV_ctrl_stim.addLayout(layH_ctrl_stim_formula)

        layH_ctrl_stim = QHBoxLayout()
        layH_ctrl_stim.addLayout(layV_ctrl_stim)
        layH_ctrl_stim.addStretch(10)
        self.wdg_ctrl_stim = QWidget(self)
        self.wdg_ctrl_stim.setLayout(layH_ctrl_stim)

        # frequency related widgets require special handling as they are scaled with f_s
        self.ledFreq1.installEventFilter(self)
        self.ledFreq2.installEventFilter(self)
        self.led_T1.installEventFilter(self)
        self.led_T2.installEventFilter(self)
        self.led_TW1.installEventFilter(self)
        self.led_TW2.installEventFilter(self)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # --- run control ---
        self.led_N_start.editingFinished.connect(self.update_N)
        self.led_N_points.editingFinished.connect(self.update_N)

        # --- frequency control ---
        # careful! currentIndexChanged passes the current index to _update_win_fft
        self.cmb_win_fft.currentIndexChanged.connect(self._update_win_fft)
        self.ledWinPar1.editingFinished.connect(self._read_param1)
        self.ledWinPar2.editingFinished.connect(self._read_param2)

        # --- stimulus control ---
        self.chk_stim_options.clicked.connect(self._show_stim_options)

        self.chk_stim_bl.clicked.connect(self._enable_stim_widgets)
        self.chk_step_err.clicked.connect(self._enable_stim_widgets)
        self.cmbStimulus.currentIndexChanged.connect(self._enable_stim_widgets)

        self.cmbNoise.currentIndexChanged.connect(self._update_noi)
        self.ledNoi.editingFinished.connect(self._update_noi)
        self.ledAmp1.editingFinished.connect(self._update_amp1)
        self.ledAmp2.editingFinished.connect(self._update_amp2)
        self.ledPhi1.editingFinished.connect(self._update_phi1)
        self.ledPhi2.editingFinished.connect(self._update_phi2)
        self.led_BW1.editingFinished.connect(self._update_BW1)
        self.led_BW2.editingFinished.connect(self._update_BW2)

        self.cmbImpulseType.currentIndexChanged.connect(self._update_impulse_type)
        self.cmbSinusoidType.currentIndexChanged.connect(self._update_sinusoid_type)
        self.cmbChirpType.currentIndexChanged.connect(self._update_chirp_type)
        self.cmbPeriodicType.currentIndexChanged.connect(self._update_periodic_type)
        self.cmbModulationType.currentIndexChanged.connect(self._update_modulation_type)
        
        self.ledDC.editingFinished.connect(self._update_DC)
        self.ledStimFormula.editingFinished.connect(self._update_stim_formula)
        self.ledStimPar1.editingFinished.connect(self._update_stim_par1)

#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the monitored widgets (ledFreq1 and 2 and T1 / T2).
        Source and type of all events generated by monitored objects are passed
         to this eventFilter, evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (``QEvent.FocusIn``), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (``QEvent.FocusOut``), store
          current value normalized to f_S with full precision (only if
          ``spec_edited == True``) and display the stored value in selected format

          Emit 'ui_changed':'stim'
        """
        def _reload_entry(source):
            """ Reload text entry for active line edit field in rounded format """
            if source.objectName() == "stimFreq1":
                source.setText(str(params['FMT'].format(self.f1 * self.f_scale)))
            elif source.objectName() == "stimFreq2":
                source.setText(str(params['FMT'].format(self.f2 * self.f_scale)))
            elif source.objectName() == "stimT1":
                source.setText(str(params['FMT'].format(self.T1 * self.t_scale)))
            elif source.objectName() == "stimT2":
                source.setText(str(params['FMT'].format(self.T2 * self.t_scale)))
            elif source.objectName() == "stimTW1":
                source.setText(str(params['FMT'].format(self.TW1 * self.t_scale)))
            elif source.objectName() == "stimTW2":
                source.setText(str(params['FMT'].format(self.TW2 * self.t_scale)))


        def _store_entry(source):
            if self.spec_edited:
                if source.objectName() == "stimFreq1":
                   self.f1 = safe_eval(source.text(), self.f1 * self.f_scale,
                                            return_type='float') / self.f_scale
                   source.setText(str(params['FMT'].format(self.f1 * self.f_scale)))

                elif source.objectName() == "stimFreq2":
                   self.f2 = safe_eval(source.text(), self.f2 * self.f_scale,
                                            return_type='float') / self.f_scale
                   source.setText(str(params['FMT'].format(self.f2 * self.f_scale)))
                elif source.objectName() == "stimT1":
                   self.T1 = safe_eval(source.text(), self.T1 * self.t_scale,
                                            return_type='float') / self.t_scale
                   source.setText(str(params['FMT'].format(self.T1 * self.t_scale)))
                elif source.objectName() == "stimT2":
                   self.T2 = safe_eval(source.text(), self.T2 * self.t_scale,
                                            return_type='float') / self.t_scale
                   source.setText(str(params['FMT'].format(self.T2 * self.t_scale)))
                elif source.objectName() == "stimTW1":
                   self.TW1 = safe_eval(source.text(), self.TW1 * self.t_scale,
                                        sign='pos', return_type='float') / self.t_scale
                   source.setText(str(params['FMT'].format(self.TW1 * self.t_scale)))
                elif source.objectName() == "stimTW2":
                   self.TW2 = safe_eval(source.text(), self.TW2 * self.t_scale,
                                        sign='pos', return_type='float') / self.t_scale
                   source.setText(str(params['FMT'].format(self.TW2 * self.t_scale)))

                self.spec_edited = False # reset flag
                self.sig_tx.emit({'sender':__name__, 'ui_changed':'stim'})

            # nothing has changed, but display frequencies in rounded format anyway
            else:
                _reload_entry(source)
        # --------------------------------------------------------------------

#        if isinstance(source, QLineEdit):
#        if source.objectName() in {"stimFreq1","stimFreq2"}:
        if event.type() in {QEvent.FocusIn,QEvent.KeyPress, QEvent.FocusOut}:
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                self.update_freqs()
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True # entry has been changed
                key = event.key()
                if key in {Qt.Key_Return, Qt.Key_Enter}:
                    _store_entry(source)
                elif key == Qt.Key_Escape: # revert changes
                    self.spec_edited = False
                    _reload_entry(source)

            elif event.type() == QEvent.FocusOut:
                _store_entry(source)

        # Call base class method to continue normal event processing:
        return super(PlotImpz_UI, self).eventFilter(source, event)


#-------------------------------------------------------------
    def recalc_freqs(self):
        """
        Update normalized frequencies if required. This is called by via signal
        ['ui_changed':'f_S'] from plot_impz.process_sig_rx
        """
        if fb.fil[0]['freq_locked']:
            self.f1 *= fb.fil[0]['f_S_prev'] / fb.fil[0]['f_S']
            self.f2 *= fb.fil[0]['f_S_prev'] / fb.fil[0]['f_S']
            self.T1 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']
            self.T2 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']
            self.TW1 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']
            self.TW2 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']

        self.update_freqs()

        self.sig_tx.emit({'sender':__name__, 'ui_changed':'f1_f2'})

#-------------------------------------------------------------
    def update_freqs(self):
        """
        `update_freqs()` is called:

        - when one of the stimulus frequencies has changed via eventFilter()
        - sampling frequency has been changed via signal ['ui_changed':'f_S']
          from plot_impz.process_sig_rx -> self.recalc_freqs

        The sampling frequency is loaded from filter dictionary and stored as
        `self.f_scale` (except when the frequency unit is k when `f_scale = self.N`).

        Frequency field entries are always stored normalized w.r.t. f_S in the
        dictionary: When the `f_S` lock button is unlocked, only the displayed
        values for frequency entries are updated with f_S, not the dictionary.

        When the `f_S` lock button is pressed, the absolute frequency values in
        the widget fields are kept constant, and the dictionary entries are updated.

        """

        # recalculate displayed freq spec values for (maybe) changed f_S
        if fb.fil[0]['freq_specs_unit'] == 'k':
            self.f_scale = self.N
        else:
            self.f_scale = fb.fil[0]['f_S']
        self.t_scale = fb.fil[0]['T_S']

        if self.ledFreq1.hasFocus():
            # widget has focus, show full precision
            self.ledFreq1.setText(str(self.f1 * self.f_scale))

        elif self.ledFreq2.hasFocus():
            self.ledFreq2.setText(str(self.f2 * self.f_scale))

        elif self.led_T1.hasFocus():
            self.led_T1.setText(str(self.T1 * self.t_scale))

        elif self.led_T2.hasFocus():
            self.led_T2.setText(str(self.T2 * self.t_scale))

        elif self.led_TW1.hasFocus():
            self.led_TW1.setText(str(self.TW1 * self.t_scale))

        elif self.led_TW2.hasFocus():
            # widget has focus, show full precision
            self.led_TW2.setText(str(self.TW2 * self.t_scale))

        else:
            # widgets have no focus, round the display
            self.ledFreq1.setText(str(params['FMT'].format(self.f1 * self.f_scale)))
            self.ledFreq2.setText(str(params['FMT'].format(self.f2 * self.f_scale)))
            self.led_T1.setText(str(params['FMT'].format(self.T1 * self.t_scale)))
            self.led_T2.setText(str(params['FMT'].format(self.T2 * self.t_scale)))
            self.led_TW1.setText(str(params['FMT'].format(self.TW1 * self.t_scale)))
            self.led_TW2.setText(str(params['FMT'].format(self.TW2 * self.t_scale)))

#-------------------------------------------------------------
    def _show_stim_options(self):
        """
        Hide / show panel with stimulus options
        """
        self.wdg_ctrl_stim.setVisible(self.chk_stim_options.isChecked())

    def _enable_stim_widgets(self):
        """ Enable / disable widgets depending on the selected stimulus """
        self.cmb_stim = qget_cmb_box(self.cmbStimulus)
        if self.cmb_stim == "impulse":
            self.stim = qget_cmb_box(self.cmbImpulseType)
        elif self.cmb_stim == "sinusoid":
            self.stim = qget_cmb_box(self.cmbSinusoidType)
        elif self.cmb_stim == "periodic":
            self.stim = qget_cmb_box(self.cmbPeriodicType)
        elif self.cmb_stim == "modulation":
            self.stim = qget_cmb_box(self.cmbModulationType)
        else:
            self.stim = self.cmb_stim

        # read out which stimulus widgets are enabled
        stim_wdg = self.stim_wdg_dict[self.stim]

        self.lblDC.setVisible("dc" in stim_wdg)
        self.ledDC.setVisible("dc" in stim_wdg)

        self.chk_norm_impz_f.setVisible("norm" in stim_wdg)
        self.chk_norm_impz_f.setEnabled(self.cmb_stim == "impulse" and self.DC == 0\
                        and (self.noi == 0 or self.cmbNoise.currentText() == 'None'))

        self.chk_step_err.setVisible(self.stim == "step")

        self.lblStimPar1.setVisible("par1" in stim_wdg)
        self.ledStimPar1.setVisible("par1" in stim_wdg)

        self.chk_stim_bl.setVisible("bl" in stim_wdg)

        self.lblAmp1.setVisible("a1" in stim_wdg)
        self.ledAmp1.setVisible("a1" in stim_wdg)
        self.lblPhi1.setVisible("phi1" in stim_wdg)
        self.ledPhi1.setVisible("phi1" in stim_wdg)
        self.lblPhU1.setVisible("phi1" in stim_wdg)
        self.lbl_T1.setVisible("T1" in stim_wdg)
        self.led_T1.setVisible("T1" in stim_wdg)
        self.lbl_TU1.setVisible("T1" in stim_wdg)
        self.lbl_TW1.setVisible("TW1" in stim_wdg)
        self.led_TW1.setVisible("TW1" in stim_wdg)
        self.lbl_TWU1.setVisible("TW1" in stim_wdg)
        self.lblFreq1.setVisible("f1" in stim_wdg)
        self.ledFreq1.setVisible("f1" in stim_wdg)
        self.lblFreqUnit1.setVisible("f1" in stim_wdg)
        self.lbl_BW1.setVisible("BW1" in stim_wdg)
        self.led_BW1.setVisible("BW1" in stim_wdg)

        self.lblAmp2.setVisible("a2" in stim_wdg)
        self.ledAmp2.setVisible("a2" in stim_wdg)
        self.lblPhi2.setVisible("phi2" in stim_wdg)
        self.ledPhi2.setVisible("phi2" in stim_wdg)
        self.lblPhU2.setVisible("phi2" in stim_wdg)
        self.lbl_T2.setVisible("T2" in stim_wdg)
        self.led_T2.setVisible("T2" in stim_wdg)
        self.lbl_TU2.setVisible("T2" in stim_wdg)
        self.lbl_TW2.setVisible("TW2" in stim_wdg)
        self.led_TW2.setVisible("TW2" in stim_wdg)
        self.lbl_TWU2.setVisible("TW2" in stim_wdg)
        self.lblFreq2.setVisible("f2" in stim_wdg)
        self.ledFreq2.setVisible("f2" in stim_wdg)
        self.lblFreqUnit2.setVisible("f2" in stim_wdg)
        self.lbl_BW2.setVisible("BW2" in stim_wdg)
        self.led_BW2.setVisible("BW2" in stim_wdg)
        self.lblStimFormula.setVisible(self.stim == "formula")
        self.ledStimFormula.setVisible(self.stim == "formula")

        self.cmbImpulseType.setVisible(self.cmb_stim == 'impulse')
        self.cmbSinusoidType.setVisible(self.cmb_stim == 'sinusoid')
        self.cmbChirpType.setVisible(self.cmb_stim == 'chirp')        
        self.cmbPeriodicType.setVisible(self.cmb_stim == 'periodic')
        self.cmbModulationType.setVisible(self.cmb_stim == 'modulation')

        self.sig_tx.emit({'sender':__name__, 'ui_changed':'stim'})

#-------------------------------------------------------------

    def _update_amp1(self):
        """ Update value for self.A1 from QLineEditWidget"""
        self.A1 = safe_eval(self.ledAmp1.text(), self.A1, return_type='cmplx')
        self.ledAmp1.setText(str(self.A1))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'a1'})

    def _update_amp2(self):
        """ Update value for self.A2 from the QLineEditWidget"""
        self.A2 = safe_eval(self.ledAmp2.text(), self.A2, return_type='cmplx')
        self.ledAmp2.setText(str(self.A2))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'a2'})

    def _update_phi1(self):
        """ Update value for self.phi1 from QLineEditWidget"""
        self.phi1 = safe_eval(self.ledPhi1.text(), self.phi1, return_type='float')
        self.ledPhi1.setText(str(self.phi1))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'phi1'})
        
    def _update_BW1(self):
        """ Update value for self.BW1 from QLineEditWidget"""
        self.BW1 = safe_eval(self.led_BW1.text(), self.BW1, return_type='float', sign='pos')
        self.led_BW1.setText(str(self.BW1))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'BW1'})

    def _update_BW2(self):
        """ Update value for self.BW2 from QLineEditWidget"""
        self.BW2 = safe_eval(self.led_BW2.text(), self.BW2, return_type='float', sign='pos')
        self.led_BW2.setText(str(self.BW2))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'BW2'})

    def _update_phi2(self):
        """ Update value for self.phi2 from the QLineEditWidget"""
        self.phi2 = safe_eval(self.ledPhi2.text(), self.phi2, return_type='float')
        self.ledPhi2.setText(str(self.phi2))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'phi2'})

    def _update_chirp_type(self):
        """ Update value for self.chirp_type from the QLineEditWidget"""
        self.chirp_type = qget_cmb_box(self.cmbChirpType) # read current data string
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'chirp_type'})

    def _update_impulse_type(self):
        """ Update value for self.impulse_type from the QLineEditWidget"""
        self.impulse_type = qget_cmb_box(self.cmbImpulseType) # read current data string
        self._enable_stim_widgets()

    def _update_sinusoid_type(self):
        """ Update value for self.sinusoid_type from the QLineEditWidget"""
        self.sinusoid_type = qget_cmb_box(self.cmbSinusoidType) # read current data string
        self._enable_stim_widgets()

    def _update_periodic_type(self):
        """ Update value for self.periodic_type from the QLineEditWidget"""
        self.periodic_type = qget_cmb_box(self.cmbPeriodicType) # read current data string
        self._enable_stim_widgets()
        
    def _update_modulation_type(self):
        """ Update value for self.modulation_type from the QLineEditWidget"""
        self.modulation_type = qget_cmb_box(self.cmbModulationType) # read current data string
        self._enable_stim_widgets()


#-------------------------------------------------------------

    def _update_noi(self):
        """ Update type + value + label for self.noi for noise"""
        self.noise = qget_cmb_box(self.cmbNoise)
        self.lblNoi.setVisible(self.noise!='none')
        self.ledNoi.setVisible(self.noise!='none')
        if self.noise!='none':
            self.noi = safe_eval(self.ledNoi.text(), 0, return_type='cmplx')
            self.ledNoi.setText(str(self.noi))
            if self.noise == 'gauss':
                self.lblNoi.setText(to_html("&nbsp;&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Standard deviation of statistical process,"
                                       "noise power is <i>P</i> = &sigma;<sup>2</sup></span>")
            elif self.noise == 'uniform':
                self.lblNoi.setText(to_html("&nbsp;&Delta; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Interval size for uniformly distributed process "
                                       "(e.g. quantization step size for quantization noise), "
                                       "centered around 0. Noise power is "
                                       "<i>P</i> = &Delta;<sup>2</sup>/12.</span>")
            elif self.noise == 'prbs':
                self.lblNoi.setText(to_html("&nbsp;A =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Amplitude of bipolar Pseudorandom Binary Sequence. "
                                       "Noise power is <i>P</i> = A<sup>2</sup>.</span>")

            elif self.noise == 'mls':
                self.lblNoi.setText(to_html("&nbsp;A =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Amplitude of Maximum Length Sequence. "
                                       "Noise power is <i>P</i> = A<sup>2</sup>.</span>")
            elif self.noise == 'brownian':
                self.lblNoi.setText(to_html("&nbsp;&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Standard deviation of the Gaussian process "
                                       "that is cumulated.</span>")

        self.sig_tx.emit({'sender':__name__, 'ui_changed':'noi'})

    def _update_DC(self):
        """ Update value for self.DC from the QLineEditWidget"""
        self.DC = safe_eval(self.ledDC.text(), 0, return_type='cmplx')
        self.ledDC.setText(str(self.DC))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'dc'})

    def _update_stim_formula(self):
        """Update string with formula to be evaluated by numexpr"""
        self.stim_formula = self.ledStimFormula.text().strip()
        self.ledStimFormula.setText(str(self.stim_formula))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'stim_formula'})

    def _update_stim_par1(self):
        """ Update value for self.par1 from QLineEditWidget"""
        self.stim_par1 = safe_eval(self.ledStimPar1.text(), self.stim_par1,
                                   sign = 'pos', return_type='float')
        self.ledStimPar1.setText(str(self.stim_par1))
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'stim_par1'})

    # -------------------------------------------------------------------------

    def update_N(self, emit=True):
        # called directly from impz or locally
        # between local triggering and updates upstream
        """
        Update values for self.N and self.N_start from the QLineEditWidget,
        update the window and fire "ui_changed"
        """
        if not isinstance(emit, bool):
            logger.error("update N: emit={0}".format(emit))
        self.N_start = safe_eval(self.led_N_start.text(), self.N_start,
                                 return_type='int', sign='poszero')
        self.led_N_start.setText(str(self.N_start)) # update widget
        self.N_user = safe_eval(self.led_N_points.text(), self.N_user,
                                return_type='int', sign='poszero')

        if self.N_user == 0: # automatic calculation
            self.N = self.calc_n_points(self.N_user) # widget remains set to 0
            self.led_N_points.setText("0") # update widget
        else:
            self.N = self.N_user
            self.led_N_points.setText(str(self.N)) # update widget

        self.N_end = self.N + self.N_start # total number of points to be calculated: N + N_start

        # recalculate displayed freq. index values when freq. unit == 'k'
        if fb.fil[0]['freq_specs_unit'] == 'k':
            self.update_freqs()

        # FFT window needs to be updated due to changed number of data points
        self._update_win_fft(emit=False) # don't emit anything here
        if emit:
            self.sig_tx.emit({'sender':__name__, 'ui_changed':'N'})


    def _read_param1(self):
        """Read out textbox when editing is finished and update dict and fft window"""
        param = safe_eval(self.ledWinPar1.text(), self.win_dict['par'][0]['val'],
                          return_type='float')
        if param < self.win_dict['par'][0]['min']:
            param = self.win_dict['par'][0]['min']
        elif param > self.win_dict['par'][0]['max']:
            param = self.win_dict['par'][0]['max']
        self.ledWinPar1.setText(str(param))
        self.win_dict['par'][0]['val'] = param
        self._update_win_fft()

    def _read_param2(self):
        """Read out textbox when editing is finished and update dict and fft window"""
        param = safe_eval(self.ledWinPar2.text(), self.win_dict['par'][1]['val'],
                          return_type='float')
        if param < self.win_dict['par'][1]['min']:
            param = self.win_dict['par'][1]['min']
        elif param > self.win_dict['par'][1]['max']:
            param = self.win_dict['par'][1]['max']
        self.ledWinPar2.setText(str(param))
        self.win_dict['par'][1]['val'] = param
        self._update_win_fft()

#------------------------------------------------------------------------------
    def _update_win_fft(self, arg=None, emit=True):
        """
        Update window type for FFT  with different arguments:

        - signal-slot connection to combo-box -> index (int), absorbed by `arg`
                                                 emit is not set -> emit=True
        - called by _read_param() -> empty -> emit=True
        - called by update_N(emit=False)

        """
        if not isinstance(emit, bool):
            logger.error("update win: emit={0}".format(emit))
        self.window_name = qget_cmb_box(self.cmb_win_fft, data=False)
        self.win = calc_window_function(self.win_dict, self.window_name,
                                        N=self.N, sym=False)

        n_par = self.win_dict['n_par']

        self.lblWinPar1.setVisible(n_par > 0)
        self.ledWinPar1.setVisible(n_par > 0)
        self.lblWinPar2.setVisible(n_par > 1)
        self.ledWinPar2.setVisible(n_par > 1)

        if n_par > 0:
            self.lblWinPar1.setText(to_html(self.win_dict['par'][0]['name'] + " =", frmt='bi'))
            self.ledWinPar1.setText(str(self.win_dict['par'][0]['val']))
            self.ledWinPar1.setToolTip(self.win_dict['par'][0]['tooltip'])

        if n_par > 1:
            self.lblWinPar2.setText(to_html(self.win_dict['par'][1]['name'] + " =", frmt='bi'))
            self.ledWinPar2.setText(str(self.win_dict['par'][1]['val']))
            self.ledWinPar2.setToolTip(self.win_dict['par'][1]['tooltip'])


        self.nenbw = self.N * np.sum(np.square(self.win)) / (np.square(np.sum(self.win)))

        self.cgain = np.sum(self.win) / self.N # coherent gain
        self.win /= self.cgain # correct gain for periodic signals

        # only emit a signal for local triggers to prevent infinite loop:
        # - signal-slot connection passes a bool or an integer
        # - local function calls don't pass anything
        if emit is True:
            self.sig_tx.emit({'sender':__name__, 'ui_changed':'win'})
        # ... but always notify the FFT widget via sig_tx_fft
        self.sig_tx_fft.emit({'sender':__name__, 'view_changed':'win'})

    #------------------------------------------------------------------------------
    def show_fft_win(self):
        """
        Pop-up FFT window
        """
        if self.but_fft_win.isChecked():
            qstyle_widget(self.but_fft_win, "changed")
        else:
            qstyle_widget(self.but_fft_win, "normal")

        if self.fft_window is None: # no handle to the window? Create a new instance
            if self.but_fft_win.isChecked():
                # Important: Handle to window must be class attribute otherwise it
                # (and the attached window) is deleted immediately when it goes out of scope
                self.fft_window = Plot_FFT_win(self, win_dict=self.win_dict, sym=False,
                                               title="pyFDA Spectral Window Viewer")
                self.sig_tx_fft.connect(self.fft_window.sig_rx)
                self.fft_window.sig_tx.connect(self.close_fft_win)
                self.fft_window.show() # modeless i.e. non-blocking popup window
        else:
            if not self.but_fft_win.isChecked():
                if self.fft_window is None:
                    logger.warning("FFT window is already closed!")
                else:
                    self.fft_window.close()

    def close_fft_win(self):
        self.fft_window = None
        self.but_fft_win.setChecked(False)
        qstyle_widget(self.but_fft_win, "normal")


#------------------------------------------------------------------------------
    def calc_n_points(self, N_user = 0):
        """
        Calculate number of points to be displayed, depending on type of filter
        (FIR, IIR) and user input. If the user selects 0 points, the number is
        calculated automatically.

        An improvement would be to calculate the dominant pole and the corresponding
        settling time.
        """
        if N_user == 0: # set number of data points automatically
            if fb.fil[0]['ft'] == 'IIR':
                N = 100
            else:
                N = min(len(fb.fil[0]['ba'][0]),100) # FIR: N = number of coefficients (max. 100)
        else:
            N = N_user

        return N

#------------------------------------------------------------------------------

def main():
    import sys
    from pyfda.libs.compat import QApplication

    app = QApplication(sys.argv)

    mainw = PlotImpz_UI(None)
    layVMain = QVBoxLayout()
    layVMain.addWidget(mainw.wdg_ctrl_time)
    layVMain.addWidget(mainw.wdg_ctrl_freq)
    layVMain.addWidget(mainw.wdg_ctrl_stim)
    layVMain.addWidget(mainw.wdg_ctrl_run)
    layVMain.setContentsMargins(*params['wdg_margins'])#(left, top, right, bottom)

    mainw.setLayout(layVMain)


    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

    # module test using python -m pyfda.plot_widgets.plot_impz_ui