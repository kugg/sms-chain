
def normalizeNumber(num):
    # basic error checking

    # remove odd characters
    num = num.replace('-','')
    num = num.replace(' ','')

    # convert numbers to normal form (+467...)
    #if num[:2] == '07':
    #    num = '+46' + num[1:]
    countrycodes={'Sweden':'+46','Denmark':'+45'}
    operatorprefix={'Tele2':'073','Telia':'070','TDC':'54'}
    #TODO add countrycodes and operator codes!
    for country, code in countrycodes.items():
        #print num, country
	if num[:3]==code:
             return num
             #print num , country
	#else:
	#    print num, 'Unknown countrycode'

    #if num[:3] == '+46':
    #     print "Not swedish format on number:", num
    #	return None
    #elif num[:3] == '+45':
    #	print ""
    #if len(num) != 12:
    #    print "Error wrong number of digits:", num
    #    return None
 
    return num

class List:
    # On an open list everyone on the list can send to it
    # On a closed list only the admins can send to it
    TYPE_OPEN, TYPE_CLOSED = range(2)
    def __init__(self, prefix, type = TYPE_OPEN):
        self.prefix = prefix
        self.type = type
        self.list = []
        self.admins = []
        self.timestamp = False

    def addNumber(self, num):
        num = normalizeNumber(num)
        if not num:
            print "Couldn't add number"
            return False
        self.list.append(num)
        return True

    def addAdmin(self, num):
        num = normalizeNumber(num)
        if not num:
            print "Couldn't add number"
            return False
        self.admins.append(num)
        return True

    def authorizedToSend(self, num):
        num = normalizeNumber(num)
        if not num:
            print 'Wrong format'
            return False

        if self.type == self.TYPE_OPEN:
            for n in self.list:
                if n == num: return True
            return False

        if self.type == self.TYPE_CLOSED:
            for n in self.admins:
                if n == num: return True
            return False

        return False

    def fromFile(self, filename):
        return False
