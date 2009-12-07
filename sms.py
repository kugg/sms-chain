#!/usr/bin/env python

import gammu
import time
from list import *
import bogus
import sys
import traceback
import os
import glob
import Queue

TESTING = False
DELETE_READ_SMS = False     # Delete smses after they have been recieved
CLEAR_SMS_AT_START = False  # Clear phone and sim of smses during initialization
COMMAND_PREFIX = ".."       # The prefix that marks a command
ALLOW_MULTIPART = False     # Allow multipart smses
verbose = True

# Set up some example lists
catalog_path='lists/'
lists = []

def init_lists():
    """Add all catalog files in the specified path.""" 
    for infile in glob.glob(os.path.join(catalog_path, '*.cat') ):
        print "Reading %s"%infile
        ll = List()
        ll.from_file(infile)
        lists.append(ll)

def unhandled_exception_hook(errtype, value, tb):
   """Handle gammu errors separately."""
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

# 
# Basic SMS stuff
#
def delete_all_sms(sm):
    """ Delete all messages on phone and on sim"""
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

def sendSMS(sm, text, num):
    """ Send a message"""
    message = {'Text': text, 'SMSC': {'Location': 1},\
               'Number': num}
    if verbose:
        print "sending", message
        sys.stdout.flush()
    sm.SendSMS(message)

class SMSQueue:
    def __init__(self):
        self.q = Queue.Queue()

    def queueSMS(self, sm, text, num):
        self.q.put((sm,text,num))

    def sendSMSes(self):
        while not sms_queue.empty():
            sm,text,num = self.q.get()
            sendSMS(sm, text, num)

    def empty(self):
        return self.q.empty()

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

#
# Program functionality
#
commands = [("au",lambda text, d, sm, li: li.addNumber(text)),
            ("aa",lambda text, d, sm, li: li.addAdmin(text)),
            ( "d",lambda text, d, sm, li: li.removeNumber(text))]
    
sms_queue = SMSQueue()

def handle_message(text, data, sm):
    """Here we look at the message recieved and decide what to do with it"""
    fromNum = data['Number']
    tstamp = time.strftime("%H:%M", time.localtime())
    text = text.strip()

    for currentlist in lists:
        if text.startswith(currentlist.prefix):
            text = text[len(currentlist.prefix):].strip()

            # check if we have a command
            print "checking for command"
            if text.startswith(COMMAND_PREFIX) and currentlist.isAdmin(fromNum):
                text = text[len(COMMAND_PREFIX):].strip()
                print "command:", text
                for command,handler in commands:
                    if text.lower().startswith(command):
                        print "found command"
                        text = text[len(command):].strip()
                        handler(text,data,sm,currentlist)
                        return

            # Check authorization
            print "trying to repeat"
            if currentlist.authorizedToSend(fromNum):
                # Everything is in order, start sending smses

                # add optional timestamp
                response = text
                if currentlist.timestamp:
                    response = tstamp + ' ' + response

                # send away!
                for num in currentlist.list:
                    sms_queue.queueSMS(sm, response, num)
            else:
                print 'Number not authorized to send', fromNum
                if currentlist.reportUnauthorizedSMSes:
                    t = "Not sent/" + fromNum + ":" + text
                    for num in currentlist.admins:
                        sms_queue.queueSMS(sm, t, num)
            return

multipart_messages = []
def Callback(sm, type, data):
    if verbose:
        print 'Received incoming event type %s, data:' % type
        sys.stdout.flush()
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
        if ALLOW_MULTIPART:
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
            sendSMS(sm, "Too long message", data['Number'])
    else:
        text = data['Text']

    if verbose:
        print "Got sms:\n",text
        sys.stdout.flush()
    handle_message(text, data, sm)

def main():
    init_lists()

    print "starting statemachine"
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

    if CLEAR_SMS_AT_START:
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
            if not sms_queue.empty():
                sms_queue.sendSMSes()

if __name__ == '__main__' :
    main()
