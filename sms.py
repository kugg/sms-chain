#!/usr/bin/env python

import gammu
import time
from list import *
import bogus
import sys
import traceback
import os
import glob
TESTING = False
DELETE_READ_SMS = False

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
             #print value
             #main()
             print  'Gammu %s: %s' % (value[0]['Where'],value[0]['Text'])
	     try:
                 main()
             except:
                 pass

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

def delete_all_sms(sm):
    status = sm.GetSMSStatus()
    remain = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']
    start = True

    while remain > 0:
        sms = sm.GetNextSMS(Start = True, Folder = 0)
        remain = remain - len(sms)
        for m in sms:
            if verbose:
                print
                print 'Deleting'
                print '%-15s: %s' % ('Number', m['Number'])
                print '%-15s: %s' %  ('Date', str(m['DateTime']))
                print '%-15s: %s' % ('State', m['State'])
                print '\n%s' % m['Text']
            sm.DeleteSMS(Location = m['Location'], Folder = 0)

def handle_message(text, data, sm):
    fromNum = data['Number']
    tstamp = time.strftime("%H:%M", time.localtime())

    for currentlist in lists:
        if currentlist.prefix == text[:len(currentlist.prefix)]:
            # Check authorization
            if currentlist.authorizedToSend(fromNum):
                # Everything is in order, start sending smses

                # Remove prefix and add optional timestamp
                response = text[len(currentlist.prefix):]
                if currentlist.timestamp:
                    response = tstamp + ' ' + response

                # send away!
                for num in currentlist.list:
                    message = {'Text': response, 'SMSC': {'Location': 1},\
                               'Number': num}
                    if verbose:
                        print "sending", message
                    sm.SendSMS(message)
            else:
                print 'Number not authorized to send', fromNum

class MultipartSMS:
    def __init__(self, from_num, id8bit, id16bit, size):
        self.from_num = from_num
        self.id8bit = id8bit
        self.id16bit = id16bit
        self.size = size
        self.parts = []

    def same(self, from_num, id8bit, id16bit, size):
        return from_num == self.from_num and id8bit == self.id8bit\
                and id16bit == self.id16bit and self.size == size

    def add_part(self, data):
        self.parts.append(data)

    def complete(self):
        return len(self.parts) == self.size

    def get_text(self):
        text = ""
        for i in range(1,self.size+1):
            for p in self.parts:
                if p['UDH']['PartNumber'] == i:
                    text += p['Text']
        return text

multipart_messages = []
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

    if DELETE_READ_SMS:
        # for some reason the Location seem to be given in 'flat' memory format
        try:
            sm.DeleteSMS(0, data['Location'])
            #sm.DeleteSMS(data['Folder'], data['Location'])
        except gammu.ERR_EMPTY, e:
            print "Unable to delete sms: Entry is empty"

    # Handle multipart messages
    text = ""
    if data['UDH']['Type'] == 'ConcatenatedMessages':
        num = data['Number']
        id8bit = data['UDH']['ID8bit']
        id16bit = data['UDH']['ID16bit']
        size = data['UDH']['AllParts']

        new_message = True
        for m in multipart_messages:
            if m.same(num,id8bit,id16bit,size):
                new_message = False
                m.add_part(data)
                if m.complete():
                    text = m.get_text()
                    multipart_messages.remove(m)
                else:
                    return # wait for complete Message
                break
        if new_message:
            m = MultipartSMS(num, id8bit, id16bit, size)
            m.add_part(data)
            multipart_messages.append(m)
            return  # wait for complete message
    else:
        text = data['Text']

    if verbose:
        print "Got sms:\n",text
    handle_message(text, data, sm)

def main():
    init_lists()

    sm = None
    if TESTING:
        sm = bogus.StateMachine()
    else:
        sm = gammu.StateMachine()
    sm.SetDebugFile('/tmp/gammu.log')
    sm.SetDebugLevel('errorsdate')
    sm.ReadConfig()
    sm.Init()
    sm.SetIncomingCallback(Callback)
    try:
        sm.SetIncomingSMS()
    except gammu.ERR_NOTSUPPORTED:
        print 'Your phone does not support incoming SMS notifications!'

    print "Clearing old sms"
    delete_all_sms(sm)
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
            sms_status = sm.GetSMSStatus()
            print 'SIM memory free: %d'%(sms_status['SIMSize']-sms_status['SIMUsed'])
            print 'Phone memory free: %d'%(sms_status['PhoneSize']-sms_status['PhoneUsed'])

if __name__ == '__main__' :
    main()
