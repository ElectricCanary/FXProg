"""
FXCore Programmer

09/2022 by Antoine Ricoux for Electric Canary

This is a programmer for the Experimental Noize FXCore DSP.
It will only work with the Digispark firmware on the same repository.

You can program the whole 16 presets by pointing to the c array files generated by the FXCore assembler.
You can also load a program to RAM for prototyping.
The default I2C address is 0x30 but it can be changed.
"""

import usb, sys, struct, getopt, time # 1.0 not 0.4
sys.path.insert(0,"..")
from usbdevice import ArduinoUsbDevice

class DSP:
    "Everything needed to program the FXCore DSP"

    creg_received = 0
    sfr_received = 0
    mreg_received = 0
    onepreset_received = 0
    prg_received = 0
    command_status = 0
    lastcommand = 0
    pgmslots = 0xFF
    deviceID = 0
    serialID = 0

    addr = 0x30
    inputfile = [0] * 17
    size = [[] for i in range(17)]
    mreg = [[] for i in range(17)]
    creg = [[] for i in range(17)]
    sfr =  [[] for i in range(17)]
    prg = [[] for i in range(17)]
    #nbinstr = 0

    def __init__(self, usbin):
        self.theDevice = usbin

    def extract_nbinstr(self, prgnum):
        listfile = open(self.inputfile[prgnum].replace(".h",".lst"), 'r')
        for line in listfile.readlines():
            if line.startswith("Total instructions: "):
                self.nbinstr = int(line.replace("Total instructions: ",''))
        listfile.close()

    def extract_array(self, prgnum):
        split = []

        header = open(self.inputfile[prgnum], 'r')
        for line in header.readlines():
            if line.startswith("0x"):
                linesplit = line.split(", ")
                split.extend(linesplit)
        header.close()
        split = list(filter(lambda a: a != "\n", split))
        #split = [element[2:] for element in split]
        split = [y.replace('\n', '') for y in split]

        for x in range(4):
            self.size[prgnum].append(int(split[x],16))

        for x in range(self.size[prgnum][0]):
            offset = 4
            self.mreg[prgnum].append(int(split[x+offset],16))

        for x in range(self.size[prgnum][1]):
            offset = 4 + self.size[prgnum][0]
            self.creg[prgnum].append(int(split[x+offset],16))

        for x in range(self.size[prgnum][2]):
            offset = 4 + self.size[prgnum][0] + self.size[prgnum][1]
            self.sfr[prgnum].append(int(split[x+offset],16))

        for x in range(self.size[prgnum][3]):
            offset = 4 + self.size[prgnum][0] + self.size[prgnum][1] + self.size[prgnum][2]
            self.prg[prgnum].append(int(split[x+offset],16))

    def USB_write(self, data):
        timeout = 0
        self.theDevice.write(data)
        while(1):
            timeout += 1
            if timeout >= 300:
                sys.exit("USB Write Fail")

            try:
                if self.theDevice.read() == data:
                    #print("OK")
                    break
                else:
                    sys.exit("I2C Write Fail")

            except:
                time.sleep(0.01)

    def USB_read(self, length):
        received = [] 
        timeout = 0
        while(1):
            timeout += 1
            if timeout >= 3000:
                sys.exit("USB Read Fail")

            if len(received) >= length:
                return(received)

            try:
                received.append(self.theDevice.read())
                #print("received :" + hex(received[len(received)-1]))
                timeout = 0

            except:
                time.sleep(0.01)

    def status_extract(self, status):
        self.creg_received = status[2] & 0b1
        self.sfr_received = (status[2] & 0b10) >> 1
        self.mreg_received = (status[2] & 0b100) >> 2
        self.onepreset_received = (status[2] & 0b1000) >> 3
        self.prg_received = (status[2] & 0b10000) >> 4
        self.command_status = status[3]
        self.lastcommand = (status[4] << 8) + status[5]
        self.pgmslots = (status[6] << 8) + status[7]
        self.deviceID = (status[1] << 8) + status[1]
        self.serialID = (status[11] << 24) + (status[10] << 16) + (status[9] << 8) + status[8]

        #print("creg received :" + str(self.creg_received))
        #print("sfr received :" + str(self.sfr_received))
        #print("mreg received :" + str(self.mreg_received))
        #print("onepreset received :" + str(self.onepreset_received))
        #print("prg received :" + str(self.prg_received))
        #print("command status :" + hex(self.command_status))
        #print("lastcommands :" + hex(self.lastcommand))
        #print("pgm slots :" + hex(self.pgmslots))

    def command_status_error(self):
        if (((self.command_status & 0xF0) == 0x10) or ((self.command_status & 0xF0) == 0x20) or ((self.command_status & 0xF0) == 0x30)):
            if self.command_status & 0xF == 0xF:
                self.USB_write(1)
                sys.exit("FLASH erase error")
            else:
                self.USB_write(1)
                sys.exit("FLASH write error")
        elif ((self.command_status & 0xF0) == 0x40):
            self.USB_write(1)
            sys.exit("Unknown program transfer error, state reset to STATE0")
        elif self.command_status == 0x80:
            self.USB_write(1)
            sys.exit("Calculated checksum did not match received checksum")
        elif self.command_status == 0xFC:
            self.USB_write(1)
            sys.exit("Command not allowed in current state")
        elif self.command_status == 0xFD:
            self.USB_write(1)
            sys.exit("Parameter out of range, generally from setting an invalid program slot number or count")
        elif self.command_status == 0xFE:
            self.USB_write(1)
            sys.exit("Command length error, all commands are 2 or 3 bytes")
        elif self.command_status == 0xFF:
            self.USB_write(1)
            sys.exit("Unknown command")
        else:
            self.USB_write(0)

    def check_status(self):
        self.status_extract(self.USB_read(12))
        self.command_status_error()

    def xfer_sequence (self, array, check = 0, prgnum = 0x7F):
        if prgnum == 0x7F:
            self.USB_write(len(array)>>8)
            self.USB_write(len(array) & 0xFF)
            for x in array:
                self.USB_write(x)
        else:
            self.USB_write(len(array[prgnum])>>8)
            self.USB_write(len(array[prgnum]) & 0xFF)
            for x in array[prgnum][:]:
                self.USB_write(x)
        if check == 1:
            self.USB_write(1)
            self.check_status()
        else:
            self.USB_write(0)

    def initialize(self):
        self.USB_write(self.addr)
        self.enter_prg()
        if self.serialID == 0:
            self.USB_write(0)
            self.USB_write(0)
            sys.exit("FXCore not Connected")
        print("Device ID: " + hex(self.deviceID) + "\n" + "Serial: " + hex(self.serialID) + "\n")

    def enter_prg(self):
        self.xfer_sequence([0xA5,0x5A,self.addr], 1)
        print("Entered Program Mode\n")
    
    def exit_prg(self):
        self.xfer_sequence([0x5A, 0xA5])
        print("Exited Program Mode\n")

    def return0(self):
        self.xfer_sequence([0x0D, 0x00])
        print("Returned to State0\n")

    def ram(self):
        self.xfer_sequence([0x0E, 0x00])
        print("Executed in RAM\n")

    def xfer_creg(self, prgnum):
        print("Transfering creg...\n")
        self.xfer_sequence([0x01, 0x0F])
        self.xfer_sequence (self.creg, 1, prgnum)
        if self.creg_received:
            print("creg transfert sucessful\n")
        else:
            self.USB_write(0)
            self.USB_write(0)
            sys.exit("creg not transfered correctly")

    def xfer_mreg(self, prgnum):
        print("Transfering mreg...\n")
        self.xfer_sequence([0x04, 0x7F])
        self.xfer_sequence (self.mreg, 1, prgnum)
        if self.mreg_received:
            print("mreg transfert sucessful\n")
        else:
            self.USB_write(0)
            self.USB_write(0)
            sys.exit("mreg not transfered correctly")

    def xfer_sfr(self, prgnum):
        print("Transfering sfr...\n")
        self.xfer_sequence([0x02, 0x0B])
        self.xfer_sequence (self.sfr, 1, prgnum)
        if self.sfr_received:
            print("sfr transfert sucessful\n")
        else:
            self.USB_write(0)
            self.USB_write(0)
            sys.exit("sfr not transfered correctly")

    def xfer_prg(self, prgnum):
        print("Transfering Program...\n")
        total = 0x0800 + self.nbinstr - 1
        self.xfer_sequence([(total & 0xFF00) >> 8, total & 0x00FF])
        self.xfer_sequence (self.prg, 1, prgnum)
        if self.prg_received:
            print("Program transfert sucessful\n")
        else:
            self.USB_write(0)
            self.USB_write(0)
            sys.exit("Program not transfered correctly")

    def write_prg(self, prgnum):
        print("Writing program to location " + str(prgnum) + "...\n")
        self.xfer_sequence([0x0C, prgnum], 1)
        print("Wrote program to location " + str(prgnum) + "\n")

    def send_preset(self, prgnum):
        self.xfer_creg (prgnum)
        self.xfer_mreg(prgnum)
        self.xfer_sfr(prgnum)
        self.xfer_prg(prgnum)

def main(argv):

    try:
        opts, args = getopt.getopt(argv,"h0:1:2:3:4:5:6:7:8:9:a:b:c:d:e:f:A:M:",["ifile=","addr="])
    except getopt.GetoptError:
      sys.exit('Argument not recognized')

    try:
        theDevice = ArduinoUsbDevice(idVendor=0x16c0, idProduct=0x05df)
    except:
        sys.exit("No DigiUSB Device Found")

    FXCore = DSP(theDevice)

    for opt, arg in opts:
        if opt in ("-h"):
            print("\n     use: -0 \"path\FXCoreProgram.h\" -A 0x30 -M \"path\FXCoreProgram.h\"\n \n")
            print("        -0 -1 -2 -3 -4 -5 -6 -7 -8 -9 -a -b -c -d -e -f : Program the file to the corresponding place from 0 to 15 \n")
            print("        -A indicate the I2C address in hex value, default is 0x30 \n ")
            print("        -M file to run from ram (for debugging DSP, doesn't write in program memory)\n\n")

        if opt in ("-0", "--ifile"):
            FXCore.inputfile[0] = arg
        if opt in ("-1", "--ifile"):
            FXCore.inputfile[1] = arg
        if opt in ("-2", "--ifile"):
            FXCore.inputfile[2] = arg
        if opt in ("-3", "--ifile"):
            FXCore.inputfile[3] = arg
        if opt in ("-4", "--ifile"):
            FXCore.inputfile[4] = arg
        if opt in ("-5", "--ifile"):
            FXCore.inputfile[5] = arg
        if opt in ("-6", "--ifile"):
            FXCore.inputfile[6] = arg
        if opt in ("-7", "--ifile"):
            FXCore.inputfile[7] = arg
        if opt in ("-8", "--ifile"):
            FXCore.inputfile[8] = arg
        if opt in ("-9", "--ifile"):
            FXCore.inputfile[9] = arg
        if opt in ("-a", "--ifile"):
            FXCore.inputfile[10] = arg
        if opt in ("-b", "--ifile"):
            FXCore.inputfile[11] = arg
        if opt in ("-c", "--ifile"):
            FXCore.inputfile[12] = arg
        if opt in ("-d", "--ifile"):
            FXCore.inputfile[13] = arg
        if opt in ("-e", "--ifile"):
            FXCore.inputfile[14] = arg
        if opt in ("-f", "--ifile"):
            FXCore.inputfile[15] = arg
        if opt in ("-A", "--addr"):
            FXCore.addr = int(arg)
        if opt in ("-M", "--ifile"):
            FXCore.inputfile[16] = arg
    
    FXCore.initialize()
    for x in range(16):
        if FXCore.inputfile[x] != 0:
            FXCore.extract_array(x)
            FXCore.extract_nbinstr(x)
            FXCore.send_preset(x)
            FXCore.write_prg(x)
            FXCore.return0()
    FXCore.exit_prg()
    
    if FXCore.inputfile[16] != 0:
        FXCore.extract_array(16)
        FXCore.enter_prg()
        FXCore.send_preset(16)
        FXCore.ram()
    
    FXCore.USB_write(0)
    FXCore.USB_write(0)
    print("Programmer Reset")

if __name__ == "__main__":

   main(sys.argv[1:])