#! /usr/bin/python
from gnuradio.eng_option import eng_option
import wave

class converter:
    def __init__( self, sr=1e7, t2=2, delay=100 ):
        self.sample_rate = sr
        self.sr = sr/1e6 # should be 10 by default
        self.t2 = t2
        self.delay = delay
        self.high = [1]
        self.low = [0]

    def convert( self, val ):
        print "Using",self.sr,"samples per microsecond"
        if val == 52:
            return self.make_52( )
        elif val == 26:
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

if __name__ == '__main__':
    try:
        f52 = wave.open("wave52.wav","w")
        f26 = wave.open("wave26.wav","w")
    except:
        print "whoops somethings wrong..."
    
    # instantiate the converter class
    conv = converter(1e7, 2, 100)
    s52 = conv.convert(52)
    s26 = conv.convert(26)

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
    f52.writeframesraw( str(s52) )
    f26.writeframesraw( str(s26) )

    # done
    f52.close()
    f26.close()
