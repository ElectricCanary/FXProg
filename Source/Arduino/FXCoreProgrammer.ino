/*This is the firmware for a FXCore Programmer.
It is meant for the Digispark board or the Attiny85.
Essentially it's an USB to I2C translator.
TinyWireM is used for receiving data up to 16 bytes. It's not used for sending data in order to be able to send an unlimited amount of data.
*/

#include <avr/io.h>
#include <DigiUSB.h>
#include <TinyWireM.h>

#define PORT_USI PORTB
#define DDR_USI PORTB
#define SDA_PIN 0
#define SCL_PIN 2
#define PIN_USI PINB
#define BYTE_COUNT 0
#define BIT_COUNT 14

uint8_t I2C_Master(uint8_t msg, uint8_t count)
{
  USIDR = msg;
  
  USISR = (1<<USISIF)|(1<<USIOIF)|(1<<USIPF)|(1<<USIDC)|(count<<USICNT0);
  
  uint8_t temp  =  (0<<USISIE)|(0<<USIOIE)|         // Interrupts disabled
           (1<<USIWM1)|(0<<USIWM0)|                 // Set USI in Two-wire mode.
           (1<<USICS1)|(0<<USICS0)|(1<<USICLK)|     // Software clock strobe as source.
           (1<<USITC);                              // Toggle Clock Port.
  do
  { 
  _delay_us(5);
    USICR = temp;                          // Generate positve SCL edge.
    while( !(PIN_USI & (1<<SCL_PIN)) );// Wait for SCL to go high.
  _delay_us(4);
    USICR = temp;                          // Generate negative SCL edge.
  }while( !(USISR & (1<<USIOIF)) );        // Check for transfer complete.
  
  _delay_us(5);
  temp  = USIDR;
  USIDR = 0xFF;                            // Release SDA.
  DDR_USI |= (1<<SDA_PIN);             // Enable SDA as output.
  return(temp);
}

uint8_t I2C_send_byte(uint8_t msg)
{
  PORT_USI &= ~(1<<SCL_PIN);                // Pull SCL LOW.
  DDR_USI   |= (1<<SDA_PIN);               // Enable SDA as output.
  I2C_Master(msg, BYTE_COUNT);
  DDR_USI  &= ~(1<<SDA_PIN);                // Enable SDA as input.
  if((I2C_Master(0xFF, BIT_COUNT) & 1) == 0)
  {
    DigiUSB.println(msg);
    DigiUSB.delay(10);
    return(0);
  }
  else
  {
    DigiUSB.println(msg+1);
    DigiUSB.delay(10);
    return(1);
  }
}

void I2C_Start()
{
/* Release SCL to ensure that (repeated) Start can be performed */
  PORT_USI |= (1<<SCL_PIN);                     // Release SCL.
  while( !(PORT_USI & (1<<SCL_PIN)) );          // Verify that SCL becomes high.
  _delay_us(5);

/* Generate Start Condition */
  PORT_USI &= ~(1<<SDA_PIN);                    // Force SDA LOW.
  _delay_us(4);                         
  PORT_USI &= ~(1<<SCL_PIN);                    // Pull SCL LOW.
  PORT_USI |= (1<<SDA_PIN);                     // Release SDA.
}

void I2C_Stop()
{
  PORT_USI &= ~(1<<SDA_PIN);           // Pull SDA low.
  PORT_USI |= (1<<SCL_PIN);            // Release SCL.
  while( !(PIN_USI & (1<<SCL_PIN)) );  // Wait for SCL to go high.  
  _delay_us(4);
  PORT_USI |= (1<<SDA_PIN);            // Release SDA.
  _delay_us(5);
}

uint8_t USB_rx(uint8_t confirm)
{
  uint8_t read;
  while(true)
  {
    if(DigiUSB.available())
    {
      read = DigiUSB.read();
      DigiUSB.delay(10);
      if(confirm == 1)
      {
        DigiUSB.println(read);
        DigiUSB.delay(10);
      }
      return(read);
    }
    else
    {
      DigiUSB.delay(10);
    }
  }
}

uint8_t check_status(uint8_t addr)
{
  TinyWireM.requestFrom(addr, 12);
  while (TinyWireM.available())
  {
    uint8_t c = TinyWireM.receive();
    DigiUSB.write(c);
    DigiUSB.delay(10);
  }
  return(USB_rx(1));
}

uint8_t i2c_sequence(uint8_t addr)
{
  int length;
  
  length = USB_rx(1)<<8;
  length += USB_rx(1);
  if (length == 0)
  {
    return(1);
  }
  I2C_Start();
  I2C_send_byte(addr<<1);
  for(int x = 0; x < length; x++)
  {
    if(I2C_send_byte(USB_rx(0)))
    {
      return(1);
    }
    DigiUSB.delay(10);
  }
  I2C_Stop();
  if (USB_rx(1))
  {
    
    return(check_status(addr));
  }
  else
  {
    return(0);
  }
}

void setup() {
  DigiUSB.begin();
  TinyWireM.begin();
}

void loop() {
  char i2c_addr;

  i2c_addr = USB_rx(1);
  while(true)
  {
    if(i2c_sequence(i2c_addr))
    {
      break;
    }
  }
}
