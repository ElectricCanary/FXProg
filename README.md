# FXCore_Programmer
The FXProg is a cheap and simple programmer for the Experimental Noize FXCore DSP using the Digispark.

## Hardware
All you need is a Digispark and two pull-up resistors. An AVR programmer is optionnal.

You can program the Digispark normally via USB by using the Arduino sketch in "Sources\Arduino". Don't forget to follow [these steps](http://digistump.com/wiki/digispark/tutorials/connecting) if it's your first time programming a Digispark.

If you're using a single ATtiny85 or you want to avoid the bootloader and its long bootup sequence, you can upload "FXCore_Programmer.hex" to the ATtiny85 with an AVR Programmer of your choice.
The right fuses are : l: 0xe1 h: 0xdd e: 0xfe

The connection between the programmer and the FXCore is pretty simple:

Connect PinB0 (physical pin 5) of the programmer to the SDA pin of the FXCore.
Connect PinB2 (physical pin 7) of the programmer to the SCL pin of the FXCore.
Connect both pull-up resistors to +3V3 (1k or 4k7 should be fine).

## Software
First of all you'll need to install the DigiUSB driver in the "DigiUSB Windows Driver" folder (It's a direct copy of [digistump's repository](https://github.com/digistump/DigisparkExamplePrograms/tree/master/C%2B%2B/DigiUSB%20Windows%20Driver)).

### Command Line
Once the programmer is properly recognized as "DigiUSB", you can use "FXCore_Programmer.exe" in command line.
Here's what -h returns :

    use: -0 "path\FXProg.h" -A 0x30 -M "path\FXCoreProgram.h"
    
    -0 -1 -2 -3 -4 -5 -6 -7 -8 -9 -a -b -c -d -e -f : Program the file to the corresponding slot from 0 to 15
    -A indicate the I2C address in hex value, default is 0x30
    -M file to run from ram (for debugging DSP, doesn't write in program memory)
    
The program takes c array files as inputs. These c array files have to be created by the FXCore Assembler with the -c option. They aren't created by default, a correct assembler instruction would be : FXCoreCmdAsm.exe -c foo foo -a "path\FXCoreProgram.fxc"
That part is taken care of in Notepad++.
    
### Notepad++
A portable version of notepad++ is included. It has custom macros under the "run" menu for programming the FXCore with DigiUSB. With this you can write and test programs under the same roof.
It's running the FXCore Assembler and FXProg via .cmd files.
