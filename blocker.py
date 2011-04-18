#! /usr/bin/python
from gnuradio import gr, gru, audio, eng_notation, window, usrp
from usrpm import usrp_dbid
from gnuradio.eng_option import eng_option
from gnuradio.qtgui import qtgui
from PyQt4 import QtGui
from decimal import *
import sys, sip, time

class receive_path(gr.hier_block2):
    def __init__(self):
        gr.hier_block2.__init__(self, "rx_path", 
                                gr.io_signature(0, 0, 0),
                                gr.io_signature(0, 0, 0))

        self.frequency = 13.56e6
        self.gain = 10

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
        usrp_decim = 1024
        self.u_rx.set_decim_rate(usrp_decim)
        #BW = 64 MS/s / decim = 64,000,000 / 256 = 250 kHz
        #Not sure if this decim rate exceeds USRP capabilities,
        #if it does then some software decim may have to be done as well
        usrp_rx_rate = adc_rate / usrp_decim

        self.iir = gr.single_pole_iir_filter_ff(.001)
        self.mag = gr.complex_to_mag()
        self.snk = gr.probe_signal_f()

        # dst = audio.sink (sample_rate, "")
        # stv = gr.stream_to_vector (gr.sizeof_float, fft_size)
        # c2m = gr.complex_to_mag_squared (fft_size)
        
        self.connect(self.u_rx, self.mag, self.iir, self.snk)

class transmit_path(gr.hier_block2):
    def __init__(self):
        gr.hier_block2.__init__(self, "tx_path", 
                                gr.io_signature(0, 0, 0),
                                gr.io_signature(0, 0, 0))

        self.frequency = 13.56e6
        self.normal_gain = 100
        self.k = 0
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
        self.subdev_tx.set_gain(self.normal_gain)

        #Tune the center frequency
        self.u_tx.tune(0, self.subdev_tx, self.frequency)

        self.src = gr.wavfile_source("wave52.wav", True)
        self.conv = gr.float_to_complex()
        self.amp = gr.multiply_const_cc(10.0 ** (self.normal_gain / 20.0))
        
        self.connect(self.src, self.conv, self.amp, self.u_tx)

    def set_amp(self, enable):
        if self.k == 0:
            self.k = self.amp.k()
        if enable:
            print "Turning blocking on!"
            t = self.k
        else:
            print "Turning blocking off!"
            t = 0
        self.amp.set_k( t )
        print "Within set_amp, k is",t

    def get_amp(self):
        # this tells if the amp is on or not
        # forgive us.
        # print "Checking amp. We're at",self.amp.k()
        return abs(self.amp.k()) > 0


class my_top_block(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        self.tx_path = transmit_path()
        self.rx_path = receive_path()

        self.connect(self.tx_path)
        self.connect(self.rx_path)

def main():
    tb = my_top_block()
    tb.start()
    thres = round(10**(Decimal(tb.rx_path.gain)/Decimal(10)),0) * 50
    print "Threshold is",thres
    tb.tx_path.set_amp(False)
    last,a,t = 0,0,0
    old_time = 0
    time_counter = 0
    start_time = 0
    big_time = 0
    while 1:
        old_time = t
        start_loop_time = time.time()
        tmp = tb.rx_path.snk.level()
        if tmp == last:
            pass
        else:
            last = tmp
            this_value = tb.rx_path.snk.level()
            if this_value > thres:
                # aa = time.time()
                # if it's over the threshold
                # and we ain't blocking
                # start blocking
                if not tb.tx_path.get_amp():
                    tb.tx_path.set_amp(True)
                # keep track of # of reads over the threshold
                # for 2 seconds.
                time_counter += 1
                if (time.time() - start_time) < 2:
                    pass
                else:
                    start_time = time.time()

        if start_loop_time != old_time \
                and time_counter > 0:
            print time_counter,"\t@\t",t,\
                "near",int(this_value),"\tmag"
            big_time += time_counter
            time_counter = 0
        # print "time.time()-start_time",time.time()-start_time
        # print "big_time",big_time
        if (time.time() - start_time > 1) and big_time > 0:
            print "Total Reads:",big_time
            big_time = 0
            # turn off blocking
            tb.tx_path.set_amp(False)
            print "Sleeping for a second"
            time.sleep(1)
            print "Awake"

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Done"
