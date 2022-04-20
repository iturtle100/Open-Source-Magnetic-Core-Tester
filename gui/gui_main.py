import PySimpleGUI as sg
#import init_cap_ps5000a
from datetime import datetime
import time
import json

sg.theme('Reddit')

#global scope probe config parameters
probe_v_max = 1
probe_v_gain = 1
probe_i_gain = 1
load_flag = False

#load scope probe config file and parse data
def get_scope_params():
    global probe_i_gain, probe_v_max, probe_v_gain
    settings = open(r"probe_config.txt", "r")
    lines = settings.readlines()
    for i in lines:
        if 'v_max' in i:
            probe_v_max = float( ''.join(filter(str.isdigit, i) ) )
        elif 'v_gain' in i:
            probe_v_gain = float(''.join(filter(str.isdigit, i) ) )
        elif 'i_gain' in i:
            probe_i_gain = float(''.join(filter(str.isdigit, i) ) )

#load scope probe config file
get_scope_params()

print('Scope Settings: ')
print('Voltage Probe: ')
print('Probe Vmax: ' + str(probe_v_max))
print('Probe Attenuation: ' + str(probe_v_gain))
print('Current Probe: ')
print('Probe Igain: ' + str(probe_i_gain))

textsize = 20

MLINE_KEY = '-ML-'+sg.WRITE_ONLY_KEY

layout = [
	[sg.Text('Please input parameters for test')],
	[sg.Text('Number of Tests',size=(textsize,1)),sg.InputText(key='-numTests-',size=(textsize,50))],
	[sg.Text('Minimum Frequency (Hz)',size=(textsize,1)),sg.InputText(key='-minFreq-',size =(textsize,50))],
	[sg.Text('Maximum Frequency (Hz)',size=(textsize,1)), sg.InputText(key='-maxFreq-',size=(textsize,50))],
	[sg.Text('Primary Turns',size=(textsize,1)), sg.InputText(key='-primaryTurn-',size = (textsize,50))],
	[sg.Text('Secondary Turns',size=(textsize,1)), sg.InputText(key='-secondaryTurn-',size = (textsize,50))],
        [sg.Text('Minimum Test Voltage (V)',size=(textsize,1)),sg.InputText(key='-minV-',size = (textsize,50))],
        [sg.Text('Maximum Test Voltage (V)',size=(textsize,1)),sg.InputText(key='-maxV-',size = (textsize,50))],
        [sg.Text('Voltage Step Size (V)',size=(textsize,1)),sg.InputText(key='-vstep-',size = (textsize,50))],
        [sg.Text('Ae (m^2)',size=(textsize,1)), sg.InputText(key='-area-',size = (textsize,50))],
	[sg.Button('Start'),sg.Button('Load State'), sg.Button('Save State'), sg.Cancel()],
        [sg.Multiline('', background_color = 'white', size=(50,10), key=MLINE_KEY)],
        [sg.Text('',size=(0,1)),sg.InputText(key='-TextBox-'), sg.Button('Enter')]
]

window = sg.Window("Alpha Demo GUI", layout, finalize=True)
sg.cprint_set_output_destination(window, MLINE_KEY) #set output destination for text window element

while True:
    #begin state machine
    event,values = window.read()
    
    if event in (sg.WIN_CLOSED, 'Exit'):
        break




    ##############################################################
    ##############################################################
    ######### START ##############################################
    ##############################################################
    ##############################################################
    if event == 'Start':

        if(not load_flag):
            #read in new values if you are not loading a state
            numTests = int(values['-numTests-'])
            minfreq = int(values['-minFreq-'])
            maxfreq = int(values['-maxFreq-'])
            Np = int(values['-primaryTurn-'])
            Ns = int(values['-secondaryTurn-'])
            Ae = float(values['-area-'])
            Vmin = int(values['-minV-'])
            Vmax = int(values['-maxV-'])
            Vstep = int(values['-vstep-'])


        if Vmax*Ns/Np >= probe_v_max or Vmin*Ns/Np >= probe_v_max:
            
            #print('Warning: Secondary coil voltage may exceed probe voltage rating. Edit probe config file, primary coil voltage level, or transformation ratio before trying again.')
            msg = 'Warning: Secondary coil voltage may exceed probe voltage rating. Edit probe config file, primary coil voltage level, or transformation ratio before trying again.'
            sg.cprint(msg, c='white on red')
        elif minfreq > maxfreq or numTests <= 0 or Vmax < Vmin or Vmax > 1000 or Vmin < 10:
            #error
            #print("Error: please check test parameters")
            msg = 'Error: please check test parameters'
            sg.cprint(msg, c='white on red')
        elif numTests >= 1 and minfreq != maxfreq:
            if numTests > 1:
                f_step = int((maxfreq - minfreq)/(numTests - 1))
                freqs = list(range(minfreq, maxfreq+1, f_step))
                
                #v_step = int((Vmax - Vmin)/(numTests - 1))
                vtests = list(range(Vmin, Vmax+1, Vstep))
            else:
                freqs = [minfreq]
                vtests = minV
                
            print(freqs)
            print(vtests)
            msg = 'Beginning Test...'
            sg.cprint(msg, c='black on white') 
            event,values = window.read(timeout=10)
            for x in vtests:
                sg.cprint('Set voltage level to ' + str(int(x)) + ' V. Y = Continue, N = Cancel', c='blue on white') 
                event,values = window.read(timeout=10)
                
                while event != 'Enter':
                    event,values = window.read(timeout=10)
                    #window.refresh()
                    #wait here until enter button is pressed
                                            
                if window['-TextBox-'].get() == 'Y':
                    #print('Continue')
                    window['-TextBox-'].update('')
                    for i in freqs: 
                        f = int(i)
                        event,values = window.read(timeout=10)    
                        #print('Running test: ' + str(f) + ' Hz')
                        msg = 'Running test: ' + str(f) + ' Hz'
                        sg.cprint(msg, c='black on white')  
                        
                        current_time = datetime.now()
                        dt_string = current_time.strftime("_%d_%m_%Y_%H-%M-%S")
                        #print("date and time =", dt_string)	
                        filename = 'test_freq_' +str(f) + dt_string + '.txt'
                        #print(filename)
                        #init_cap_ps5000a.run_ps5000a(filename, f, Np, Ns, Ae)
                        time.sleep(0.1)
                elif window['-TextBox-'].get() == 'N':
                    print('Cancel')
                else:
                    print('No valid input')
                    
                window['-TextBox-'].update('')
                
            msg = 'Test complete'
            sg.cprint(msg, c='white on green')
    
    #############################################################################
    #############################################################################
    ###################### SAVE STATE ###########################################
    #############################################################################
    #############################################################################
    if event == 'Save State':
        try:
            numTests_store = int(values['-numTests-'])
            minfreq_store = int(values['-minFreq-'])
            maxfreq_store = int(values['-maxFreq-'])
            Np_store = int(values['-primaryTurn-'])
            Ns_store = int(values['-secondaryTurn-'])
            Ae_store = float(values['-area-'])
            Vmin_store = int(values['-minV-'])
            Vmax_store = int(values['-maxV-'])
            Vstep_store = int(values['-vstep-'])

            #store to json file
            json_dict = {}
            json_dict['numTests'] = numTests_store
            json_dict['minfreq'] = minfreq_store
            json_dict['maxfreq'] = maxfreq_store
            json_dict['Np'] = Np_store
            json_dict['Ns'] = Ns_store
            json_dict['Ae'] = Ae_store
            json_dict['Vmin'] = Vmin_store
            json_dict['Vmax'] = Vmax_store
            json_dict['Vstep'] = Vstep_store

            json_string = json.dumps(json_dict)
            
            store_filename = sg.popup_get_text("Please enter filename: ")
            store_filename = store_filename + ".json"
            with open(store_filename,'w') as store_file:
                store_file.write(json_string)

            sg.cprint("State has been saved successfully!", c = "blue on white")
        
        #handle exception for if not all values are defined
        except ValueError:
            message = "Please define parameters in text boxes above"
            sg.cprint(message,c="blue on white")
        



    ##############################################################################
    ##############################################################################
    ################### LOAD STATE ###############################################
    ##############################################################################
    ##############################################################################
    if event == 'Load State':
        #open json file
        filename = sg.popup_get_file('Load State', no_window=True,file_types=(("JSON Files", "*.json"),))
        state = open(filename)
        state_params = json.load(state)

        #extract parameters from saved state
        numTests = state_params["numTests"]
        minfreq = state_params["minfreq"]
        maxfreq = state_params["maxfreq"]
        Np = state_params["Np"]
        Ns = state_params["Ns"]
        Ae = state_params["Ae"]
        Vmin = state_params["Vmin"]
        Vmax = state_params["Vmax"]
        Vstep = state_params["Vstep"]

        #confirm that state has been loaded via text box
        msg = "The state from {} has been loaded\nThe parameters are now:".format(filename)
        sg.cprint(msg,c="blue on white")

        for attribute,value in state_params.items():
            msg = "{}:{}".format(attribute,value)
            sg.cprint(msg,c="blue on white")

        load_flag = True
        
        state.close()	
		



window.close()
