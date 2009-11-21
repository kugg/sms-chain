#!/usr/bin/env python

import gammu
import time
from list import *
import bogus

TESTING = True

# Whether be a bit more verbose
verbose = True

# Set up some example lists
admins_file='./admins.txt'
catalog_file='./numbers.txt'

try:
   catalog=open(catalog_file,'r')
   all=catalog.read().split()
   catalog.close()
except IOError:
   try:
      print 'Created empty catalog since none existed at ' , catalog_file
      open(catalog_file, 'w').close()
   except IOError, (errno, strerror):
      print  'Could not create catalog at %s , %s' % (catalog_file, strerror)
   print 'Running with testnumbers just to get started!'
   all=['070-0000002','070-0000001']

ll1 = List('A. ')
ll2 = List('B. ', List.TYPE_CLOSED)
for num in all:
    ll1.addNumber(num)
    ll2.addNumber(num)

ll2.addAdmin('070-000 000 2')
ll2.timestamp = True

lists = [ll1,ll2]

admins = ['+46700000000']
def isAdmin(num):
    for n in admins:
        if n == num:
            return True
        print num, ' != ', n
    return False

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

    for list in lists:
        if list.prefix == data['Text'][:len(list.prefix)]:
            fromNum = data['Number']

            # Check authorization
            if isAdmin(fromNum) or list.authorizedToSend(fromNum):
                # Everything is in order, start sending smses

                # Remove prefix and add optional timestamp
                response = data['Text'][len(list.prefix):]
                if list.timestamp:
                    response = tstamp + ' ' + response

                # send away!
                for num in list.list:
                    message = {'Text': response, 'SMSC': {'Location': 1}, 'Number': num}
                    if verbose:
                        print "sending", message
                    sm.SendSMS(message)
            else:
                print 'Number not authorized to send', fromNum

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
