#! /usr/bin/python
# requires:
# sudo apt-get install gnuradio python-numpy python-setuptools g++ python-dev libaudiere-dev 
# http://pyaudiere.org/
from gnuradio.eng_option import eng_option
import wave
import pylab
import audiere
import os

class converter:
    def __init__( self, sr=1e7, t2=2.5, delay=100 ):
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
            print "[+] Making 52."
            return self.make_52( )
        elif val == 26:
            print "[+] Making 26."
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
        binary = list(bin(int(str(hexn),16))[2:])
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

# class SoundFile:
#     def  __init__(self, signal, filename, duration=1, samplerate=44100):
#         self.file = wave.open(filename, 'wb')
#         self.signal = signal
#         self.sr = samplerate
#         self.duration = duration
  
#     def write(self):
#         self.file.setparams((1, 2, self.sr, self.sr*self.duration, 'NONE', 'noncompressed'))
#         # setparams takes a tuple of:
#         # nchannels, sampwidth, framerate, nframes, comptype, compname
#         self.file.writeframes(self.signal)
#         self.file.close()

if __name__ == '__main__':
    f52_file = 'wave52_n.wav'
    f26_file = 'wave26_n.wav'

    try:
        f52 = wave.open(f52_file,"wb")
        f26 = wave.open(f26_file,"wb")
    except:
        print "whoops somethings wrong..."
    
    # instantiate our converter class
    # samples/sec, t2 (gap), trailing Ys
    conv = converter(4e6, 3, 20)
    s52 = conv.convert(52)
    s26 = conv.convert(26)

    print "[+] Using 52:"
    print "[+] Duration",len(s52)
    print "[+] First 100 frames:"
    print s52[:100]

    # convert to binary
    s52_out = "".join((wave.struct.pack('h', item) for item in s52))
    s26_out = "".join((wave.struct.pack('h', item) for item in s26))

    print "[+] Attempting to write."

    # make the wave header
    # The tuple should be (nchannels, sampwidth, 
    # framerate, nframes, comptype, compname), 
    # with values valid for the set*() methods.
    # Sets all parameters.
    f52.setparams((1, 2, conv.sample_rate, \
                       len(s52_out), 'NONE', 'not compressed'))
    f26.setparams((1, 2, conv.sample_rate, \
                       len(s26_out), 'NONE', 'not compressed'))

    f52.writeframes( s52_out )
    f26.writeframes( s26_out )

    # done
    f52.close()
    f26.close()

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
