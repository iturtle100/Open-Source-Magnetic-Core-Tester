# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 16:23:48 2021

@author: Mark
"""

import numpy as np
import matplotlib.pyplot as plt
import pickle
from scipy import optimize
from scipy import integrate
from scipy import signal

def cyclical_sse(t, B, period, steps):
    """Calculate Cyclical Sum Squared Error of vectors t,B with scalar period t_period
    t - Vector of times (s)
    B - Vector of field intensity (T)
    period - Cycle period (s)
    steps - Number of steps to solve for per period
    """
    error = 0
    t_step = period/steps
    for _t  in np.arange(0, period, t_step):
        # Make vector of sample times on each cycle
        times = np.arange(_t, t[-1], period)
        ## Linearly interpolate B values at time sample points
        Bset = np.interp(times, t, B)
        Bavg = np.sum(Bset)/len(Bset)
        error += np.sum((Bset - Bavg)**2)
    return error

def error_func(x, t, B, period, steps):
    """Error function to pass to scipy minimzer"""
    B_new = B + np.arange(len(B)) * x
    return cyclical_sse(t, B_new, period, steps)

def analyze_bh(filename, Np, Ns, Ae, f):
    ## Setup
    le = np.pi * (138.85e-3 + 134.05e-3)/2     # Mean magnetic path length (m)
    # Ae = 44.65e-3 * (138.85e-3 - 134.05e-3)/2     # Effective magnetic area (m^2)
    #Ae = 0.0000882    # From Metglas accounting for packing factor
    
    # Input low pass filtering
    FILTER_INPUTS = True    # Low pass filter inputs
    n_taps = 200
    cutoff_freq_hz = 1e3
    # Linear integrator correction
    USE_LINEAR_CORRECTION = True
    
    ## Import data
    data = np.genfromtxt(filename,delimiter=',', skip_header=1)
    t = data[:,0]/1000000
    Vs = data[:,1]/1000  # Chan 1, secondary voltage
    Ip = data[:,2]/1000  # Chan 2
    
    ## Check data
    assert(np.all(np.isfinite(Ip)))
    assert(np.all(np.isfinite(Vs)))
    assert(np.all(np.isfinite(t)))
    
    # Vs_freq_rms = np.fft.rfft(Vs)/len(Vs)
    # Vs_freq_rms = 2*np.abs(Vs_freq_rms)       # 'Fold FFT'
    # Vs_freq_rms[0] /= 2                          # Correct DC value
    # Vs_freq_rms = Vs_freq_rms/np.sqrt(2)      # Find RMS from amplitude
    # Vs_freq_rms[0] *= np.sqrt(2)                 # RMS value of DC doesn't need 'correction'
    # fundamentalIndex = np.argwhere(Vs_freq_rms == np.max(Vs_freq_rms))
    
    # fig, ax = plt.subplots()
    # ax.scatter(np.arange(len(Vs_freq_rms)), Vs_freq_rms, s=0.1)
    
    if FILTER_INPUTS:  
        ## Create linear phase FIR low pass filter for input data
        taps = signal.firwin(n_taps, cutoff_freq_hz, pass_zero='lowpass', fs=1/(t[1]-t[0])) 
        ## Plot filter function
        w,h = signal.freqz(taps, fs=1/(t[1]-t[0])) 
        fig,ax = plt.subplots()
        ax.plot(w, 20 * np.log10(abs(h)),'b')
        plt.grid()
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude [dB]')
        plt.title('Filter Response')
        ax2 = ax.twinx()
        angles = np.unwrap(np.angle(h))
        plt.plot(w, angles, 'g')
        plt.ylabel('Angle (rad)', color='g')
        plt.xlim((0, w[-1]))
        ## All signls MUST be filtered together due to filter delay (fixed group delay)
        ## Remove elements from begining to allow for filter settling
        Vs = signal.lfilter(taps,[1], Vs)[n_taps:]
        Ip = signal.lfilter(taps,[1], Ip)[n_taps:]
        t = t[0:-n_taps]    # Remove end elements so time still starts at zero
    
    ## Plot traces
    fig, ax = plt.subplots()
    ax.scatter(t*1000, Vs, marker='.', s=1, alpha=0.2, c='r')
    plt.xlabel('time (ms)')
    plt.ylabel('Voltage (V)')
    ax2 = ax.twinx()
    ax2.scatter(t*1000, Ip, marker='.', s=1, alpha=0.2, c='g')
    plt.ylabel('Current (A)')
    plt.title('Test Waveforms')
    # plt.grid()   # TODO: Want horizontal grid lines to match on both sides
    # plt.xlim(0, t[-1])
    #plt.legend(('Vsec', 'Ipri'))
    # fig.tight_layout()
    
    ## Calculate B-H loop for entire data window
    H = (Np * Ip) / le
    B = integrate.cumtrapz(Vs, t, initial=0) / (Ns*Ae)
    
    if USE_LINEAR_CORRECTION:
        if t[-1]-t[0] < 2/f:
            raise Exception('Linear correction requires a capture of at least 2 full cycles')
        ## Find linear integrator correction for BH loop
        opt_result = optimize.minimize_scalar(error_func, args=(t,B,1/f,1000))
        if opt_result.success == False:
            raise Exception('Linear integration correction failed. Usually this is caused by core sat.')
        print('Corrected linearity SSE = ' + str(opt_result.fun))
        # Apply linear integrator correction
        B += np.arange(len(B))*opt_result.x
        
        
        
    ## Remove DC offset in B. W
    # Find end index of first cycle
    cycle_idx = int(1/(f*(t[1]-t[0])))
    # Offset B by the average B of the first cycle
    B = B - np.sum(B[0:cycle_idx]) / cycle_idx
    # TODO: If the data has multiple cycles, maybe we can use more than 1 cycle to 
    # in this correction

    # Manual linearity correction
    x = cyclical_sse(t, B, 1/f, 1000)
    print('SSE = ' + str(x)) 
    B = B + t * 1           
    x = cyclical_sse(t, B, 1/f, 1000)
    print('SSE = ' + str(x))


    ## Plot B-H
    fig, ax = plt.subplots()
    ax.scatter(H, B, marker='.', s=.1, alpha=0.2)
    # Force a symetric window
    xmax = 1.1* np.max(np.abs(H))
    plt.xlim((-xmax,xmax))
    ymax = 1.1* np.max(np.abs(B))
    plt.ylim((-ymax,ymax))
    plt.title('GMLC Test Core ' + str(f) + 'hz')
    ax.set_xlabel('H (A/m)')
    ax.set_ylabel('B (T)')
    ax.grid()

    ## Average a single cycle to obtain DC values for each trace
    samples_per_cycle = int(1/(f*(t[1]-t[0])))
    Ipri_dc = np.sum(Ip[0:samples_per_cycle])/samples_per_cycle
    Vsec_dc = np.sum(Vs[0:samples_per_cycle])/samples_per_cycle
    dc_current_ratio = Ipri_dc/np.max(np.abs(Ip))

    print('Ipri_DC/Ipri_peak = ' + str(Ipri_dc))
    print('dc current ratio = ' + str(dc_current_ratio))

    #plt.draw()
    #plt.show()
        
        
        
        