#!/usr/bin/env python
import usb.core
import usb.util
import sys
import requests
import json
import websocket
import time

dev = None
ep = None

def connect_to_scanner():
	# find our zebra device
	dev = usb.core.find(idVendor = 0x05e0, idProduct = 0x0600)
	
	# was it found ?
	if dev is None:
	    	print('Device not found (meaning it is disconnected)')
		return (None, None)
	
	# detach the kernel driver so we can use interface (one user per interface)
	reattach = False
	print(dev.is_kernel_driver_active(0))
	if dev.is_kernel_driver_active(0):
		print("Detaching kernel driver")
    		reattach = True
    		dev.detach_kernel_driver(0)
	
	# set the active configuration; with no arguments, the first configuration
	# will be the active one
	dev.set_configuration()
	
	# get an endpoint instance
	cfg = dev.get_active_configuration()
	interface_number = cfg[(0, 0)].bInterfaceNumber
	alternate_setting = usb.control.get_interface(dev, interface_number)
	intf = usb.util.find_descriptor(
    		cfg, bInterfaceNumber = interface_number,
    		bAlternateSetting = alternate_setting
	)
	
	ep = usb.util.find_descriptor(
    		intf,
    		# match the first OUT endpoint
    		custom_match = \
    		lambda e: \
        		usb.util.endpoint_direction(e.bEndpointAddress) == \
        		usb.util.ENDPOINT_IN)
	
	assert ep is not None 
	return (dev, ep)

(dev, ep) = connect_to_scanner()	

while 1:
    try:
        # read data
        data = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize * 2, 1000)
        str = ''.join(chr(i) if i > 0 and i < 128 else '' for i in data)
        str = str.rstrip()[1:]
	# barcode saved to str
	print str
    except Exception as e:
        error_code = e.args[0]
        # 110 is timeout code, expected
        if error_code == 110:
        	print "device connected, waiting for input"
	else:
		print(e)
        	print "device disconnected"
		(dev, ep) = connect_to_scanner()
		if dev is None and ep is None:
			time.sleep(1)
