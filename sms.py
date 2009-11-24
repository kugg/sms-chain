#!/usr/bin/env python

import gammu
import time
from list import *
import bogus
import sys
import traceback
import os
import glob
TESTING = True

verbose = True

# Set up some example lists
catalog_path='lists/'
lists = []

def init_lists():
    # add all catalog files in the specified path
    for infile in glob.glob(os.path.join(catalog_path, '*.cat') ):
        print "Reading %s"%infile
        ll = List()
        ll.from_file(infile)
        lists.append(ll)

def unhandled_exception_hook(errtype, value, tb):
   #handle gammu errors separately
   gammu_names=dir(gammu)
   for gammu_name in gammu_names:
      if 'ERR'==gammu_name[:3]:
         #print errtype.__name__, gammu_name
         if gammu_name==errtype.__name__:
             print value
  	     return 0
 
   if errtype==KeyboardInterrupt:
      print 'Goodbye!'
      sys.exit(0)
   elif errtype==MemoryError:
      print 'Running our of memory!'
      print value
      print tb
   elif errtype==SystemExit:
      pass
      #Take away potential pidfile if we are daemon.
   else:
      print 'Unhandled error:', errtype, value , traceback.tb_lineno(tb)
      sys.exit(1)

sys.excepthook = unhandled_exception_hook

# TODO handle lists so that they can be rw'es from more then one sources...

def Callback(sm, type, data):
    if verbose:
        print 'Received incoming event type %s, data:' % type
    if type != 'SMS':
        print 'Unsupported event!'
        return 
    if not data.has_key('Number'):
        data = sm.GetSMS(data['Folder'], data['Location'])[0]
    if verbose:
        print data

    tstamp = time.strftime("%H:%M", time.localtime())

    for currentlist in lists:
        if currentlist.prefix == data['Text'][:len(currentlist.prefix)]:
            fromNum = data['Number']

            # Check authorization
            if currentlist.authorizedToSend(fromNum):
                # Everything is in order, start sending smses

                # Remove prefix and add optional timestamp
                response = data['Text'][len(currentlist.prefix):]
                if currentlist.timestamp:
                    response = tstamp + ' ' + response

                # send away!
                for num in currentlist.list:
                    message = {'Text': response, 'SMSC': {'Location': 1}, 'Number': num}
                    if verbose:
                        print "sending", message
                    sm.SendSMS(message)
            else:
                print 'Number not authorized to send', fromNum

def main():
    init_lists()

    sm = None
    if TESTING:
        sm = bogus.StateMachine()
    else:
        sm = gammu.StateMachine()

    sm.ReadConfig()
    sm.Init()
    sm.SetIncomingCallback(Callback)
    try:
        sm.SetIncomingSMS()
    except gammu.ERR_NOTSUPPORTED:
        print 'Your phone does not support incoming SMS notifications!'

    if TESTING:
        while 1:
            print 'Write a message:'
            x = raw_input()
            sm.gotsms(x)
    else:
        # We need to keep communication with phone to get notifications
        print 'Press Ctrl+C to interrupt'
        while 1:
            time.sleep(1)
            status = sm.GetBatteryCharge()
            print 'Battery is at %d%%' % status['BatteryPercent']

if __name__ == '__main__' :
    main()
