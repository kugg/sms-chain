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
    """Takes a phone number string and massages it, removing bad
    characters, and parsing from which country the number came from,
    and which operator carries the number."""
    # basic error checking

    # remove odd characters
    num = num.replace('-','')
    num = num.replace(' ','')

    # convert numbers to normal form (+467...)
    #if num[:2] == '07':
    #    num = '+46' + num[1:]
    countrycodes = {
        'Sweden': '+46',
        'Denmark': '+45',
        'Uk': '+44',
    }
    operatorprefix = {
        'tdc': '',
        'sonofon': '',
        'orange': '',
        'telia': '',
        'tre': '',
    }
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
    """An SMS recipient list.
    Everyone can send to an open list.
    Only the admins can send to a closed list.
    """
    TYPE_OPEN, TYPE_CLOSED = range(2)
    def __init__(self, filename=None):
        """Initialize List, optionally from given filename."""
        self.prefix = None
        self.type = self.TYPE_CLOSED
        self.timestamp = False
        self.list = []
        self.admins = []
        self.filename = filename
        if self.filename:
            self.from_file(self.filename)

    def from_file(self, filename):
        """Load up List from given filename."""
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

    def to_file(self, filename):
        """Persists List to given filename."""
        s = ""
        s += "# prefix = '%s'\n"%self.prefix
        s += "# type = %s\n"%('open' if self.type == self.TYPE_OPEN else 'closed')
        s += "# timestamp = %s\n"%('yes' if self.timestamp else 'no')
        for num in self.admins:
            s += "!" + num + "\n"
        for num in self.list:
            if num not in self.admins:
                s += num + "\n"
        outfile = open(filename, 'w')
        outfile.write(s)
        outfile.close()

    def addNumber(self, num):
        """Add given phone number to recipient List."""
        num = normalizeNumber(num)
        if not num:
            print "Couldn't add number"
            return False

        if not num in self.list:
            self.list.append(num)
            if self.filename:
                outfile = open(self.filename, "a")
                outfile.write(num+'\n')
                outfile.close()

        return True

    def addAdmin(self, num):
        """Add given phone number as administrator of recipient List."""
        num = normalizeNumber(num)
        if not num:
            print "Couldn't add number"
            return False
        if not num in self.list:
            self.list.append(num)
        if not num in self.admins:
            self.admins.append(num)
        if self.filename:
            self.to_file(self.filename)
        return True

    def removeNumber(self, num):
        """Remove number from list"""
        num = normalizeNumber(num)
        if num in self.admins:
            self.admins.remove(num)
        if num in self.list:
            self.list.remove(num)


    def authorizedToSend(self, num):
        """Returns true if given phone number has send privileges on this List."""
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

    def isAdmin(self, num):
        return num in self.admins

    def fromFile(self, filename):
        return False

    def __str__(self):
        """String representation of of List."""
        s = "Prefix = %s\n"%self.prefix
        if self.type == self.TYPE_OPEN:
            s += "Open list\n"
        else:
            s += "Closed list\n"
        s += "Timestamp: %s\n"%self.timestamp
        s += "Admins:\n"
        for a in self.admins:
            s += a + "\n"
        s += "Users:\n"
        for u in self.list:
            s += u + "\n"
        return s
