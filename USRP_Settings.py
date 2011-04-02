#==========================To create a TX instance of the USRP===================================

self.u_tx = usrp.sink_c()  #create the USRP sink
dac_rate = self.u.dac_rate()        
usrp_interpol = 256     #pure guesswork/filler value
self.u_tx.set_interp_rate(usrp_interpol)
usrp_tx_rate = dac_rate / usrp_interpol
        
if options.tx_subdev_spec is None:          #This block lets us search for a daughterboard to use
    options.tx_subdev_spec = pick_subdevice(self.u_tx)

#The following two set the daughterboard to be used
self.u_tx.set_mux(usrp.determine_tx_mux_value(self.u_tx,options.tx_subdev_spec)) 
self.subdev = usrp.selected_subdev(self.u_tx, options.tx_subdev_spec)
print "Using TX dboard %s" % (self.subdev.side_and_name(),) #Just a quick sanity check to make sure the right board is being used



#=============================To create a RX instance of the USRP==========================================================

self.u_rx = usrp.source_c() #create the USRP source for RX
rx_subdev_spec = usrp.pick_subdev(self.u_rx, (usrp_dbid.LF_RX, usrp_dbid.LF_TX)) #try and set the LF_RX for this

self.u_rx.set_mux(usrp.determine_rx_mux_value(self.u_rx, rx_subdev_spec))  #Configure the MUX for the daughterboard
self.subdev_rx = usrp.selected_subdev(self.u_rx, rx_subdev_spec)           #Tell it to use the LF_RX
print "Using RX dboard %s" % (self.subdev_rx.side_and_name(),)             #Make sure it worked 


adc_rate = self.u_rx.adc_rate() #64 MS/s
usrp_decim = 1024       
self.u_rx.set_decim_rate(usrp_decim)
usrp_rx_rate = adc_rate / usrp_decim    #BW = 64 MS/s / decim = 64,000,000 / 1024 = 62.5kHz  Not sure if this decim rate exceeds USRP capabilities, if it does then some software decim may have to be done as well
