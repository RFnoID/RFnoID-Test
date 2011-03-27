#! /usr/bin/python
from gnuradio import gr, gru, audio, eng_notation, window
from gnuradio.eng_option import eng_option
import sys
# gui
from gnuradio.wxgui import stdgui2, fftsink2, waterfallsink2, scopesink2, form, slider
from optparse import OptionParser
import wx

class our_test(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        sample_rate = 48000
        ampl = 0.1
        fft_size = 256
        freq1 = 350
        freq2 = 440
        src0 = gr.sig_source_f (sample_rate, gr.GR_SIN_WAVE, freq1, ampl)
        src1 = gr.sig_source_f (sample_rate, gr.GR_SIN_WAVE, freq2, ampl)
        fft0 = src0
        fft1 = src1

        mywindow = window.blackmanharris(fft_size)
        fft = gr.fft_vfc(fft_size, True, mywindow)
        power = 0
        for tap in mywindow:
            power += tap*tap

        fdst = gr.file_sink (2048, "hello.out")
        dst = audio.sink (sample_rate, "")
        self.connect (src0, (dst, 0))
        self.connect (src1, (dst, 1))
        stv = gr.stream_to_vector (gr.sizeof_float, fft_size)
        self.connect (src0, stv, fft, fdst)


if __name__ == '__main__':
    try:
        our_test().run()
    except KeyboardInterrupt:
        print "whoops"

