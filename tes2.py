#! /usr/bin/python
from gnuradio import gr
from gnuradio.qtgui import qtgui

from PyQt4 import QtGui
import sys, sip

class my_tb(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        # Make a local QtApp so we can start it from our side
        self.qapp = QtGui.QApplication(sys.argv)

        fftsize = 2048

        self.src = gr.sig_source_c(1, gr.GR_SIN_WAVE, 0.1, 1)
        self.nse = gr.noise_source_c(gr.GR_GAUSSIAN, 0.1)
        self.add = gr.add_cc()
        self.thr = gr.throttle(gr.sizeof_gr_complex, 100*fftsize)
        self.snk = qtgui.sink_c(fftsize, gr.firdes.WIN_BLACKMAN_hARRIS)
        
        self.connect(self.src, (self.add, 0))
        self.connect(self.nse, (self.add, 1))
        self.connect(self.add, self.thr, self.snk)

        # Tell the sink we want it displayed
        self.pyobj = sip.wrapinstance(self.snk.pyqwidget(), QtGui.QWidget)
        self.pyobj.show()

def main():
    tb = my_tb()
    tb.start()
    tb.qapp.exec_()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

