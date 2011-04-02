#! /usr/bin/python
from gnuradio import gr, gru, audio, eng_notation, window, usrp
from usrpm import usrp_dbid
from gnuradio.eng_option import eng_option
from gnuradio.qtgui import qtgui
from PyQt4 import QtGui
from decimal import *
import sys, sip, time

class our_test(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        self.frequency = 13.56e6
        self.gain = 100
        self.usrp_interpol = 128

        # USRP settings
        self.u_tx = usrp.sink_c() #create the USRP sink for TX
        #try and set the LF_RX for this
        self.tx_subdev_spec = usrp.pick_subdev(self.u_tx, (usrp_dbid.LF_RX, usrp_dbid.LF_TX))
        #set the interpolation rate to match the USRP's 128 MS/s
        self.u_tx.set_interp_rate(self.usrp_interpol)

        #Configure the MUX for the daughterboard
        self.u_tx.set_mux(usrp.determine_tx_mux_value(self.u_tx, self.tx_subdev_spec))
        #Tell it to use the LF_TX
        self.subdev_tx = usrp.selected_subdev(self.u_tx, self.tx_subdev_spec)
        #Make sure it worked 
        print "Using TX dboard %s" % (self.subdev_tx.side_and_name(),)             

        #Set gain.. duh
        self.subdev_tx.set_gain(self.gain)

        #Tune the center frequency
        self.u_tx.tune(0, self.subdev_tx, self.frequency)

        self.src = gr.wavfile_source("carrier_test_1M.wav", True)
        self.conv = gr.float_to_complex()
        self.amp = gr.multiply_const_cc(10.0 ** (self.gain / 20.0))
        
        self.connect(self.src, self.conv, self.amp, self.u_tx)

def main():
    ot = our_test()
    ot.run()
            
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "whoops"

