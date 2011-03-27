#! /usr/bin/python
from gnuradio import gr, gru, audio, eng_notation, window
from gnuradio.eng_option import eng_option
from gnuradio.qtgui import qtgui
from PyQt4 import QtGui
import sys, sip
# gui
# from gnuradio.wxgui import stdgui2, fftsink2, waterfallsink2, scopesink2, form, slider
# from optparse import OptionParser
# import wx

class our_test(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        # Make a local QtApp so we can start it from our side
        self.qapp = QtGui.QApplication(sys.argv)

        sample_rate = 48000
        ampl = 1
        fft_size = 256
        freq1 = 3500
        freq2 = 440
        self.src0 = gr.sig_source_f (sample_rate, gr.GR_SIN_WAVE, freq1, ampl)
        self.nse = gr.noise_source_f (gr.GR_GAUSSIAN, 0.1)
        #src1 = gr.sig_source_f (sample_rate, gr.GR_SIN_WAVE, freq2, ampl)
        #fft0 = src0
        #fft1 = src1
        self.add = gr.add_ff()
#        self.thr = gr.throttle(gr.sizeof_gr_complex, 100*fft_size)
#        self.snk = qtgui.sink_c(fft_size, gr.firdes.WIN_BLACKMAN_hARRIS)
        self.snk = gr.probe_signal_f() 
        mywindow = window.blackmanharris(fft_size)
        fft = gr.fft_vfc(fft_size, True, mywindow)
        power = 0
        for tap in mywindow:
            power += tap*tap

        #fdst = gr.file_sink (1024, "hello.out")
        dst = audio.sink (sample_rate, "")
        # self.connect (src0, (dst, 0))
        # self.connect (src1, (dst, 1))
        stv = gr.stream_to_vector (gr.sizeof_float, fft_size)
        c2m = gr.complex_to_mag_squared (fft_size)
        #self.connect (dst, stv, fft, c2m, fdst)
        self.connect(self.src0, (self.add, 0))
        self.connect(self.nse, (self.add, 1))
        self.connect(self.add, self.snk)
        # Tell the sink we want it displayed
#        self.pyobj = sip.wrapinstance(self.snk.pyqwidget(), QtGui.QWidget)
 #       self.pyobj.show()


def main():
    ot = our_test()
    ot.start()
    while 1:
        print ot.snk.level()
#        raw_input('Press Enter to quit:')
#    ot.qapp.exec_()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "whoops"

