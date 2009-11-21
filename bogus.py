class StateMachine:
    def __init__(self):
        self.callback = None
    def SendSMS(self, message):
        print "Bogus sending sms: ", message
    def ReadConfig(self):
        pass
    def Init(self):
        pass
    def SetIncomingCallback(self, fn):
        self.callback = fn
    def SetIncomingSMS(self):
        pass
    def GetBatteryCharge(self):
        return 100

    def gotsms(self, msg):
        data = {'Number': '', 'Text': msg }
        self.callback(self, 'SMS', data)
