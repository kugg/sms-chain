#!/usr/bin/env python

import gammu
import time
from list import *
import bogus
import sys

TESTING = True

# Whether be a bit more verbose
verbose = True

# Set up some example lists
admin_file='./admins.txt'
catalog_file='./numbers.txt'


def unhandled_exception_hook(type, value, traceback):
   if type==KeyboardInterrupt:
      print 'Goodbye!'
      sys.exit(0)
   elif type==MemoryError:
      print 'Running our of memory!'
      print value
      print traceback
   elif type==SystemExit:
      pass
      #Take away potential pidfile if we are daemon.
   print 'Unhandled error:', type, value
   sys.exit(1)

sys.excepthook = unhandled_exception_hook


try:
   admincatalog=open(admin_file,'r')
   admins=admincatalog.read().split()
   
   if len(admins)<1:
      raise UserWarning (1, 'Nothing in there!')

except IOError, (errno, strerror):
   print 'Warning: Could not find configuraiton file for admins in %s , %s' % (admin_file, strerror)
   print 'Warning: Not using any admins!'
   admins=[]

except UserWarning, (errno, strerror):
   print 'Warning: Problem with admin configuration! in %s , %s' % (admin_file, strerror)
   print 'Warning: Not using any admins!'
   admins=[]

try:
   usercatalog=open(catalog_file,'r')
   users=usercatalog.read().split()
   usercatalog.close()

   if len(users)<1:
      raise UserWarning (1, 'Nothing in there!')
	 
except IOError, (errno, strerror):
   print 'Warning: Could not read recipients catalog file %s, %s' % (catalog_file, strerrror )
   print 'Warning: Not using any recipients!'
   users=[]

except UserWarning, (errno, strerror):
   print 'Warning: Problem with recipients catalog in %s , %s' % (catalog_file, strerror)
   print 'Warning: Not using any recipients!'
   users=[]

if users==[] and admins==[]:
   print 'Error: You dont have neither Admins nor Users so this setup is useless! Create at least one admin account.'
   sys.exit(1)

#This stuff is an example and not proper service operation code. TODO handle lists so that they can be rw'es from more then one sources...
ll1 = List('A. ')
ll2 = List('B. ', List.TYPE_CLOSED)
for num in users:
    ll1.addNumber(num)
    ll2.addNumber(num)

ll2.addAdmin('+447785016005')
ll2.timestamp = True

lists = [ll1,ll2]

#admins = ['+447785016005']
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
	print '\nChoose an action:\n------------------\n1) add a recipient\n2) add an admin\n3) send message\n4) show lists\n6) write message\n'
	m = raw_input("choose an option: > ")
	if m == "1":
		print "\nAdd recipient:"
		a = raw_input()
		users = 
	elif m == "2":
		print "\nAdd admin.."
	elif m == "3":
		print "\nSend message?"
	elif m == "4":
		print "\nshow lists...\n"
		print users
	elif m == "6":
		print '\nWrite a message:'
	        x = raw_input()
		sm.gotsms(x)
	else:
		print "wrong choice"

else:
    # We need to keep communication with phone to get notifications
    print 'Press Ctrl+C to interrupt'
    while 1:
        time.sleep(1)
        status = sm.GetBatteryCharge()
        print 'Battery is at %d%%' % status['BatteryPercent']
