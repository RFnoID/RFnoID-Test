#! /usr/bin/python
# requires:
# sudo apt-get install gnuradio python-numpy python-setuptools g++ python-dev libaudiere-dev 
# http://pyaudiere.org/
from gnuradio.eng_option import eng_option
import wave
import pylab
import audiere

class converter:
    def __init__( self, sr=1e7, t2=2, delay=100 ):
        self.sample_rate = sr
        self.sr = sr/1e6 # should be 10 by default
        self.t2 = t2
        self.delay = delay
        self.high = [0xFF] # 100% ASK
        self.low = [0x00]

    def convert( self, val ):
        print "[+] Using",self.sr,"samples per microsecond."
        if val == 52:
            print "[+] Making 52."
            return self.make_52( )
        elif val == 26:
            print "[+] Making 26"
            return self.make_26( )

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
        binary = list(bin(int(hexn,16))[2:])
        for b in binary:
            bit = int(b)
            if bit == 1:
                out.append( self.x() )
            elif bit == 0 and pbit < 1:
                # two or more contiguous 0's
                out.append( self.z() )
            else: # bit is 0 and pbit is 1
                out.append( self.y() )
            pbit = bit
        return out + self.y()*self.delay

if __name__ == '__main__':
    try:
        f52 = wave.open("wave52.wav","w")
        f26 = wave.open("wave26.wav","w")
    except:
        print "whoops somethings wrong..."
    
    # instantiate our converter class
    conv = converter(1e7, 2, 100)
    s52 = conv.convert(52)
    s26 = conv.convert(26)

    print "[+] Attempting to write."
    print "[+] First 100 frames:"
    print s52[:100]

    # make the wave header
    # The tuple should be (nchannels, sampwidth, 
    # framerate, nframes, comptype, compname), 
    # with values valid for the set*() methods.
    # Sets all parameters.
    f52.setparams((1, 2, conv.sample_rate, \
                       len(s52), 'NONE', 'NONE'))
    f26.setparams((1, 2, conv.sample_rate, \
                       len(s26), 'NONE', 'NONE'))

    # write audio frames, without correcting nframes
    # TODO: http://codingmess.blogspot.com/2008/07/how-to-make-simple-wav-file-with-python.html
    for i in range(len(s52)):
        f52.writeframes( str(s52[i]) )

    for i in range(len(s26)):
        f26.writeframes( str(s26[i]) )

    # done
    f52.close()
    f26.close()

    print "[+] Write succeeded."
    print "[+] Attempting to read the first 100 frames back."

    # test section: read it back.
    w = wave.open('wave52.wav','r')
    l = w.getnframes()

    if l > 100:
        l = 100

    for i in range(l):
        print w.readframes(1),
        w.setpos(i)
