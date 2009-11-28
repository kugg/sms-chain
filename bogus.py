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
    def GetSMSStatus(self):
        """Returns data block describing phone memory status."""
        sms_status = dict(
            SIMUnRead=5,
            SIMUsed=8,
            SIMSize=100,
            PhoneUnRead=2,
            PhoneUsed=19,
            PhoneSize=200,
        )
        return sms_status

    def gotsms(self, msg):
        data = {'Number': '+447785016005', 'Text': msg }
        self.callback(self, 'SMS', data)
