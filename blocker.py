#! /usr/bin/python
from gnuradio import gr, gru, audio, eng_notation, window, usrp
from usrpm import usrp_dbid
from gnuradio.eng_option import eng_option
from gnuradio.qtgui import qtgui
from PyQt4 import QtGui
from decimal import *
import sys, sip, time
import wave
import pylab
import audiere
import os
import optparse

SAMPLERATE = 0

class converter:
    def __init__( self, sr=1e6, t2=3, delay=30 ):
        self.sample_rate = sr
        # to get sample rate into microseconds
        self.sr = sr/1e6
        self.t2 = t2
        self.delay = delay
        self.high = [0x7FFF] # 100% ASK
        self.low = [0x0000]
        self.duration = 0

    def convert( self, val ):
        print "[+] Using",self.sr,"samples per microsecond."
        if val == 52:
            print "[+] Making 52 using the build in method."
            return self.make_52( )
        elif val == 26:
            print "[+] Making 26 using the build in method."
            return self.make_26( )
        else:
            return self.make_n( val )

    # seq_x( t2, sampling rate )
    # first part = [high]*(sampling rate)*4.72 microseconds times
    # second part = [low]*(sampling rate)*t2
    # third part = [high]*(sampling rate)*(4.72-t2) # 9.44-4.72-t2
    # returns list of first second and third parts
    def x( self ):
        return self.high*int(round(self.sr*4.72)) + \
            self.low*int(round(self.sr*self.t2)) + \
            self.high*int(round(self.sr*(4.72-self.t2)))

    # seq_y( sampling rate )
    # returns [high]*(sampling rate)*9.44
    def y( self ):
        return self.high*int(round(self.sr*9.44))

    # seq_z( t2, sampling rate )
    # first part = [low]*(sampling rate)/t2
    # second part = [high]*(sampling rate)/(9.44-t2)
    def z( self ):
        return self.low*int(round(self.sr*self.t2)) + \
            self.high*int(round(self.sr*(9.44-self.t2)))

    # make_52( delay=100 )
    # returns Z Z X Y Z X Y X [Y]*delay
    def make_52( self ):
        return self.z() + self.z() + self.x() + self.y() + \
            self.z() + self.x() + self.y() + self.x() + \
            self.y()*self.delay

    # make_26( delay=100 )
    # returns Z Z X X Y Z X Y Z [Y]*delay
    def make_26( self ):
        return self.z() + self.z() + self.x() + self.x() + \
            self.y() + self.z() + self.x() + self.y() + \
            self.z() + self.y()*self.delay

    # logic "1" sequence X
    # logic 0" sequence Y with the following two exceptions:
    #    i)  If there are two or more contiguous "0"s, sequence Z
    #        shall be used from the second "0" on
    #    ii) If the first bit after a "start of frame" is "0" , sequence Z
    #        shall be used to represent this and any "0"s which follow
    #        directly thereafter
    # Start of communication sequence Z
    # End of communication logic "0" followed by sequence Y
    # No information at least two sequences Y
    # make_n returns a NFC 14443-2 compliant stream to be converted
    # into a wav file given a hex number to parse.
    def make_n( self, hexn ):
        out = self.z()
        pbit = -1
        binary = list(bin(int(str(hexn),16))[2:]).reverse()
        for b in binary:
            bit = int(b)
            if bit == 1:
                out += self.x()
            elif bit == 0 and pbit < 1:
                # two or more contiguous 0's
                out += self.z()
            else: # bit is 0 and pbit is 1
                out += self.y()
            pbit = bit
        return out + self.y()*self.delay

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
        usrp_decim = 256
        self.u_rx.set_decim_rate(usrp_decim)
        #BW = 64 MS/s / decim = 64,000,000 / 256 = 250 kHz
        #Not sure if this decim rate exceeds USRP capabilities,
        #if it does then some software decim may have to be done as well
        usrp_rx_rate = adc_rate / usrp_decim

        self.iir = gr.single_pole_iir_filter_ff(.53)
        self.mag = gr.complex_to_mag()
        self.moving = gr.moving_average_ff(2, 1, 1000)
        self.snk = gr.probe_signal_f()

        # dst = audio.sink (sample_rate, "")
        # stv = gr.stream_to_vector (gr.sizeof_float, fft_size)
        # c2m = gr.complex_to_mag_squared (fft_size)
        
        self.connect(self.u_rx, self.mag, self.moving, self.snk)

class transmit_path(gr.hier_block2):
    def __init__(self):
        gr.hier_block2.__init__(self, "tx_path", 
                                gr.io_signature(0, 0, 0),
                                gr.io_signature(0, 0, 0))

        self.frequency = 13.56e6
        self.normal_gain = 100
        self.k = 0
        self.usrp_interpol = int(128/(SAMPLERATE/1e6))
        print "[+] Using interpolation rate of",self.usrp_interpol

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
            #print "Turning blocking on!"
            t = self.k
        else:
            #print "Turning blocking off!"
            t = 0
        self.amp.set_k( t )
        # print "Within set_amp, k is",t

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

def make_wave(sr):
    print "Using sample rate of",sr
    # if not isinstance(sr, int):
    #     sr = int(sr)
    conv = converter(sr,3,30)
    f52_file = 'wave52.wav'

    try:
        f52 = wave.open(f52_file,"wb")
    except:
        print "whoops somethings wrong opening the file..."

    s52 = conv.convert(52)

    print "[+] Using 52:"
    print "[+] Duration",len(s52)
    print "[+] First 100 frames:"
    print s52[:100]

    # convert to binary
    s52_out = "".join((wave.struct.pack('h', item) for item in s52))

    print "[+] Attempting to write."

    # make the wave header
    # The tuple should be (nchannels, sampwidth, 
    # framerate, nframes, comptype, compname), 
    # with values valid for the set*() methods.
    # Sets all parameters.
    f52.setparams((1, 2, conv.sample_rate, \
                       len(s52_out), 'NONE', 'not compressed'))

    f52.writeframes( s52_out )

    # done
    f52.close()

    print "[+] Write succeeded."
    print "[+] Attempting to read the first 1,000 frames back."

    # test section: read it back.
    w = wave.open(f52_file,'r')
    l = w.getnframes()

    if l > 1000:
        l = 1000

    printout = ""
    for i in range(l):
        printout += str(w.readframes(1))
        w.setpos(i)

    f = open("blah","wb")
    f.write(printout)
    f.close()

    os.system("hexdump -C blah")

def main():
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(prog='BLOCKER',
                                   option_class=eng_option,
                                   usage=usage)
    parser.add_option('-s', '--samplerate', action='store',
                        default=1e6, type="eng_float")
    (options, args) = parser.parse_args()

    # make the wave52.wav file with the specified sample rate
    global SAMPLERATE
    SAMPLERATE = options.samplerate
    make_wave( SAMPLERATE )

    print "[+] Wave created"
    
    tb = my_top_block()
    tb.start()

    print "[+] Blocker and detector running"

    thres = round(10**(Decimal(tb.rx_path.gain)/Decimal(10)),0) * 50
    print "Threshold is",thres
    tb.tx_path.set_amp(False)
    last,a,t = 0,0,0
    old_time = 0
    time_counter = 0
    start_time = 0
    big_time = 0
    blocking = False
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
                    if not blocking:
                        print "[+] Blocking on"
                    blocking = True
                # keep track of # of reads over the threshold
                # for 2 seconds.

                time_counter += 1
                if (time.time() - start_time) < 2:
                    pass
                else:
                    start_time = time.time()

        if start_loop_time != old_time \
                and time_counter > 0:
          #  print time_counter,"\t@\t",time.clock(),\
           #     "near",int(this_value),"\tmag"
            big_time += time_counter
            time_counter = 0
        # print "time.time()-start_time",time.time()-start_time
        # print "big_time",big_time
        if (time.time() - start_time > 1) and big_time > 0:
            #print "Total Reads:",big_time
            big_time = 0
            # turn off blocking
            tb.tx_path.set_amp(False)
            print "[-] Blocking off"
            blocking = False
            #print "Awake"

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Done"
