# PS5000 BLOCK MODE EXAMPLE
# This example opens a 5000a driver device, sets up two channels and a trigger then collects a block of data.
# This data is then plotted as mV against time in ns.

import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

import bh_test
import wavegen

def run_ps5000a(filename, freq, Np, Ns, Ae):
    

        
    #convert freq into horizontal axis scaling values for scope capture
    
    # Create chandle and status ready for use
    chandle = ctypes.c_int16()
    status = {}

    # Open 5000 series PicoScope
    # Returns handle to chandle for use in future API functions
    resolution =ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]
    status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)
    assert_pico_ok(status["openunit"])

    # Set up channel A
    # handle = chandle
    channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
    # enabled = 1
    coupling_type = 1 # DC
    chARange = ps.PS5000A_RANGE["PS5000A_20V"]
    # analogue offset = 0 V
    status["setChA"] = ps.ps5000aSetChannel(chandle, channel, 1, coupling_type, chARange,0)
    assert_pico_ok(status["setChA"])

    # Set up channel B
    # handle = chandle
    channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
    # enabled = 1
    # coupling_type = ps.PS5000_COUPLING["PS5000_DC"]
    chBRange = ps.PS5000A_RANGE["PS5000A_2V"]
    # analogue offset = 0 V
    status["setChB"] = ps.ps5000aSetChannel(chandle, channel, 1, coupling_type, chBRange, 0)
    assert_pico_ok(status["setChB"])

    # find maximum ADC count value
    # handle = chandle
    # pointer to value = ctypes.byref(maxADC)
    maxADC = ctypes.c_int16(32512)

    # Set up single trigger
    # handle = chandle
    # enabled = 1
    source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
    threshold = int(mV2adc(500,chARange, maxADC))
    # direction = PS5000_RISING = 2
    # delay = 0 s
    # auto Trigger = 1000 ms
    status["trigger"] = ps.ps5000aSetSimpleTrigger(chandle, 1, source, threshold, 2, 0, 1000)
    assert_pico_ok(status["trigger"])

    # Set number of pre and post trigger samples to be collected
    preTriggerSamples = 2500
    postTriggerSamples = 2500
    maxSamples = preTriggerSamples + postTriggerSamples

    # Get timebase information
    # handle = chandle
    timebase = 8
    # noSamples = maxSamples
    # pointer to timeIntervalNanoseconds = ctypes.byref(timeIntervalns)
    oversample = 1
    # pointer to maxSamples = ctypes.byref(returnedMaxSamples)
    # segment index = 0
    timeIntervalns = ctypes.c_float()
    returnedMaxSamples = ctypes.c_int32()
    status["getTimebase2"] = ps.ps5000aGetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
    assert_pico_ok(status["getTimebase2"])

    
    wavegen.wavegen(chandle, status, freq) #configure awg output


    # Run block capture
    # handle = chandle
    # number of pre-trigger samples = preTriggerSamples
    # number of post-trigger samples = PostTriggerSamples
    # timebase = 8 = 80 ns (see Programmer's guide for mre information on timebases)
    # oversample = 1
    # time indisposed ms = None (not needed in the example)
    # segment index = 0
    # lpReady = None (using ps5000IsReady rather than ps5000BlockReady)
    # pParameter = None
    status["runBlock"] = ps.ps5000aRunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, None, 0, None, None)
    assert_pico_ok(status["runBlock"])

    # Check for data collection to finish using ps5000IsReady
    ready = ctypes.c_int16(0)
    check = ctypes.c_int16(0)
    while ready.value == check.value:
        status["isReady"] = ps.ps5000aIsReady(chandle, ctypes.byref(ready))


    # Create buffers ready for assigning pointers for data collection
    bufferAMax = (ctypes.c_int16 * maxSamples)()
    bufferAMin = (ctypes.c_int16 * maxSamples)() # used for downsampling which isn't in the scope of this example
    bufferBMax = (ctypes.c_int16 * maxSamples)()
    bufferBMin = (ctypes.c_int16 * maxSamples)() # used for downsampling which isn't in the scope of this example

    # Set data buffer location for data collection from channel A
    # handle = chandle
    source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
    # pointer to buffer max = ctypes.byref(bufferAMax)
    # pointer to buffer min = ctypes.byref(bufferAMin)
    # buffer length = maxSamples
    status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(chandle, source, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples, 0, 0)
    assert_pico_ok(status["setDataBuffersA"])

    # Set data buffer locsation for data collection from channel B
    # handle = chandle
    source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
    # pointer to buffer max = ctypes.byref(bufferBMax)
    # pointer to buffer min = ctypes.byref(bufferBMin)
    # buffer length = maxSamples
    # segment index = 0
    # ratio mode = PS5000_RATIO_MODE_NONE = 0
    status["setDataBuffersB"] = ps.ps5000aSetDataBuffers(chandle, source, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), maxSamples, 0, 0)
    assert_pico_ok(status["setDataBuffersB"])

    # create overflow loaction
    overflow = ctypes.c_int16()
    # create converted type maxSamples
    cmaxSamples = ctypes.c_int32(maxSamples)

    # Retried data from scope to buffers assigned above
    # handle = chandle
    # start index = 0
    # pointer to number of samples = ctypes.byref(cmaxSamples)
    # downsample ratio = 0
    # downsample ratio mode = PS5000_RATIO_MODE_NONE
    # pointer to overflow = ctypes.byref(overflow))
    status["getValues"] = ps.ps5000aGetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
    assert_pico_ok(status["getValues"])


    # convert ADC counts data to mV
    adc2mVChAMax =  adc2mV(bufferAMax, chARange, maxADC)
    adc2mVChBMax =  adc2mV(bufferBMax, chBRange, maxADC)

    # Create time data
    time = np.linspace(0, (cmaxSamples.value) * timeIntervalns.value, cmaxSamples.value)
    
    file = open(filename, 'w')
    
    for i in range(len(time)):
        file.write(str(time[i]/1000)+', '+ str(adc2mVChAMax[i]) +', ' + str(adc2mVChBMax[i])+'\n')

    file.close()
    
    
    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('time (us)')
    ax1.set_ylabel('Vs (mV)', color=color)
    ax1.plot(time/1000, adc2mVChAMax[:], color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Ip (mA)', color=color)  # we already handled the x-label with ax1
    ax2.plot(time/1000, adc2mVChBMax[:], color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
  
    plt.savefig('Data.png')
    
    # Stop the scope
    # handle = chandle
    status["stop"] = ps.ps5000aStop(chandle)
    assert_pico_ok(status["stop"])

    # Close unit Disconnect the scope
    # handle = chandle
    status["close"]=ps.ps5000aCloseUnit(chandle)
    assert_pico_ok(status["close"])

    bh_test.analyze_bh(filename, Np,Ns, Ae, freq)
    
    # display status returns
    print(status)