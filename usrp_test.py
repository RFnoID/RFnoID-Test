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
        self.gain = 3

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
        self.subdev_rx.set_gain(self.gain)

        #Tune the center frequency
        self.u_rx.tune(0, self.subdev_rx, self.frequency)

        adc_rate = self.u_rx.adc_rate() #64 MS/s
        usrp_decim = 8
        self.u_rx.set_decim_rate(usrp_decim)
        #BW = 64 MS/s / decim = 64,000,000 / 256 = 250 kHz
        #Not sure if this decim rate exceeds USRP capabilities,
        #if it does then some software decim may have to be done as well
        usrp_rx_rate = adc_rate / usrp_decim

        self.snk = gr.probe_avg_mag_sqrd_c(1,0.01)

        # dst = audio.sink (sample_rate, "")
        # stv = gr.stream_to_vector (gr.sizeof_float, fft_size)
        # c2m = gr.complex_to_mag_squared (fft_size)
        
        self.connect(self.u_rx, self.snk)

def main():
    ot = our_test()
    ot.start()
    thres = round(10**(Decimal(ot.gain)/Decimal(10)),0) * 100
    print "Threshold is",thres
    last,a,t = 0,0,0
    old_time = 0
    time_counter = 0
    start_time = 0
    big_time = 0
    while 1:
        old_time = t
        t = time.clock()
        tmp = ot.snk.level()
        if tmp == last:
            pass
        else:
            last = tmp
            a = ot.snk.level()
            if a > thres:
                time_counter += 1
                if (time.clock() - start_time) < 2:
                    pass
                else:
                    start_time = time.clock()
        if t != old_time and time_counter > 0:
            print time_counter,"\t@\t",t,"near",a,"mag squared"
            big_time += time_counter
            time_counter = 0
        if (time.clock() - start_time > 2) and big_time > 0:
            print "Total Reads:",big_time
            big_time = 0
            
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "whoops"

