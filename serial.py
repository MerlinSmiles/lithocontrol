import serial   # http://pyserial.sf.net

port = 0
ser = serial.Serial(port, baudrate=9600, parity=serial.PARITY_NONE, timeout=1) # opens, too.
print "Monitoring serial port " + ser.name
data = []
while True:
    ch = ser.read(1)
    if len(ch) == 0:
        # rec'd nothing print all
        if len(data) > 0:
            s = ''
            for x in data:
                s += ' %02X' % ord(x)
            print '%s [len = %d]' % (s, len(data))
        data = []
    else:
        data.append(ch)
        print ch