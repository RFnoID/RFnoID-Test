#! /usr/bin/python
from gnuradio import gr, gru, audio, eng_notation, window, usrp
from usrpm import usrp_dbid
from gnuradio.eng_option import eng_option
from gnuradio.qtgui import qtgui
from PyQt4 import QtGui
import sys, sip

class our_test(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        sample_rate = 48000
        ampl = 1
        fft_size = 256
        frequency = 13.56e6

        # USRP settings
        self.u_rx = usrp.source_c() #create the USRP source for RX
        #try and set the LF_RX for this
        rx_subdev_spec = usrp.pick_subdev(self.u_rx, (usrp_dbid.LF_RX, usrp_dbid.LF_TX))

        #Configure the MUX for the daughterboard
        self.u_rx.set_mux(usrp.determine_rx_mux_value(self.u_rx, rx_subdev_spec))
        #Tell it to use the LF_RX
        self.subdev_rx = usrp.selected_subdev(self.u_rx, rx_subdev_spec)
        #Make sure it worked 
        print "Using RX dboard %s" % (self.subdev_rx.side_and_name(),)             

        #Set gain.. duh
        self.subdev_rx.set_gain(3)

        #Tune the center frequency
        self.u_rx.tune(0, self.subdev_rx, frequency)

        adc_rate = self.u_rx.adc_rate() #64 MS/s
        usrp_decim = 256
        self.u_rx.set_decim_rate(usrp_decim)
        #BW = 64 MS/s / decim = 64,000,000 / 256 = 250 kHz
        #Not sure if this decim rate exceeds USRP capabilities,
        #if it does then some software decim may have to be done as well
        usrp_rx_rate = adc_rate / usrp_decim

        self.snk = gr.probe_avg_mag_sqrd_c(1,0.001)

        dst = audio.sink (sample_rate, "")
        stv = gr.stream_to_vector (gr.sizeof_float, fft_size)
        c2m = gr.complex_to_mag_squared (fft_size)
        
        self.connect(self.u_rx, self.snk)

def main():
    ot = our_test()
    ot.start()
    while 1:
        print ot.snk.level()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "whoops"

