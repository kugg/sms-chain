class Error(Exception):
    pass

class NumberError(Error):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ParseCatalogFileError(Error):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def normalizeNumber(num):
    # basic error checking

    # remove odd characters
    num = num.replace('-','')
    num = num.replace(' ','')

    # convert numbers to normal form (+467...)
    #if num[:2] == '07':
    #    num = '+46' + num[1:]
    countrycodes={'Sweden':'+46','Denmark':'+45','Uk':'+44'}
    operatorprefix={'tdc':'','sonofon':'','orange':'','telia':'','tre':''}
    #TODO add countrycodes and operator codes!
    for country, code in countrycodes.items():
        if num[:3]==code:
             #TODO Add country based separation here!

             # do some error checking
             if country == 'Sweden' and len(num) != 12:
                 raise NumberError('Wrong number of digits in number: %s'%num)

             return num
             #TODO Add operator based separation here!
 
    return num

class List:
    # On an open list everyone on the list can send to it
    # On a closed list only the admins can send to it
    TYPE_OPEN, TYPE_CLOSED = range(2)
    def __init__(self, filename=None):
        self.prefix = None
        self.type = self.TYPE_CLOSED
        self.timestamp = False
        self.list = []
        self.admins = []
        self.filename = filename
        if self.filename:
            self.from_file(self.filename)

    def from_file(self, filename):
        self.filename = filename
        infile = open(filename, "r")
        prefix = filename
        type = None
        timestamp = None

        # parse the header
        while infile.read(1) == '#':
            line = infile.readline()
            line = line[1:]
            if line.find('=') != -1:
                field,value = line.split('=',1)
                field = field.strip()
                value = value.strip()
                if (value[0] == "'" and value[-1] == "'")\
                  or (value[0] == '"' and value[-1] == '"'):
                    value = value[1:-1]

                if field.lower() == 'prefix':
                    prefix = value
                elif field.lower() == 'type':
                    if value.lower() == 'closed':
                        type = self.TYPE_CLOSED
                    elif value.lower() == 'open':
                        type = self.TYPE_OPEN
                    else:
                        raise ParseCatalogFileError("Unknown setting: 'type = %s'"%value)
                elif field.lower() == 'timestamp':
                    if value.lower() == 'yes':
                        timestamp = True
                    elif value.lower() == 'no':
                        timestamp = False
                    else:
                        raise ParseCatalogFileError("Unknown setting: 'timestamp = %s'"%value)
                else:
                    raise ParseCatalogFileError("Unknown setting: '%s'"%line)

        #reset the last character
        infile.seek(infile.tell()-1)

        self.prefix = prefix
        if type != None: self.type = type
        if timestamp != None: self.timestamp = timestamp
        self.list = []
        self.admins = []

        while infile:
            line = infile.readline().strip()
            if not line: break
            
            if line[0] == '!': 
                line = line[1:]
                self.admins.append(normalizeNumber(line))
            self.list.append(normalizeNumber(line))


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

    def __str__(self):
        str = "Prefix = %s\n"%self.prefix
        if self.type == self.TYPE_OPEN:
            str += "Open list\n"
        else: str += "Closed list\n"
        str += "Timestamp: %s\n"%self.timestamp
        str += "Admins:\n"
        for a in self.admins:
            str += a + "\n"
        str += "Users:\n"
        for u in self.list:
            str += u + "\n"
        return str
