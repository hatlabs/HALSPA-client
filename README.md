# HALSPA Client: Testing Libraries for HALSPA: Hat Labs Spaghetti Board

## Background

HALSPA is Hat Labs Spaghetti Board, a generic test jig interface board that sits between a bed-of-nails test fixture and a Raspberry Pi computer. It includes a Raspberry Pi Pico 2 for interfacing and orchestrating different subsystems. HALSPA can be used for rapid development of test jigs for various digital and analog circuits. It is designed to be flexible and adaptable to different test requirements.

### Hardware Features

HALSPA subsystems include:
- DUT 5V output
- DUT 3.3V output
- Two 12V current limiters: limit the current to a preset (using a potentiometer) value. If the current is exceeded, the output is immediately latched off and a fault flag is raised.
- Four 3.3V-5V current limiters that can be physically connected to the 3.3V or 5V DUTs and have limiting functionality otherwise similar to the 12V limiters
- Four current sense amplifiers with analog outputs for measuring the current in a circuit
- Four opamps configured as potentiometer-adjustable non-inverting amplifiers with emitter follower outputs. With a PWM input, these can be used to implement programmable linear power supplies with a voltage range between 0-12V.
- Two four-channel ADCs with potentiometer-adjustable input voltage dividers with an I2C interface
- Four 8-to-1 analog MUXes programmable over I2C
- Four 8-channel digital expanders with an I2C interface
- 8-channel 3.3V to 5V level shifter
- USB serial port
- USB port with remote EN for both data and VCC, for connecting to DUT test pads
- 40-pin IDC header for connecting the Pi GPIO header
- Proto pin areas for additional circuits

## Introduction

The HALSPA client library is a Python library for orchestrating the HALSPA test jig. It is designed to be used with the HALSPA hardware and provides interfaces implementing tests using PyTest. The tests interact with the `picon` MicroPython library running on the Raspberry Pi Pico 2. The tests are designed to be run on the Raspberry Pi using PyTest, which sends MicroPython snippets to the Pico 2 to run individual tests and register the test results.

It is also possible to connect the Raspberry Pi GPIO header directly to the HALSPA hardware. In this case, Raspberry Pi GPIO I/O can be used directly to interact with the HALSPA hardware.

## Getting Started with MicroPython REPL

To interact with the HALSPA hardware directly through MicroPython, you can enter the REPL with the picon modules available:

### Option 1: Upload and Enter REPL (Recommended)

```bash
cd picon
./run upload  # Upload main.py and picon/ modules to device
mpremote repl  # Enter REPL with modules available
```

### Option 2: Manual Upload

```bash
cd picon
mpremote cp -r main.py picon :  # Upload the modules manually
mpremote repl  # Enter REPL
```

### Option 3: Development Mode with Mount

```bash
cd picon
mpremote mount . repl  # Mount current directory and enter REPL
```

### Using the Hardware in REPL

Once in the REPL, you can import and use the picon modules:

```python
# Import the main picon module (has pre-initialized hardware objects)
from picon.picon import *

# Now you have access to:
# - i2c (I2C bus)
# - powcon (PowerControl instance) 
# - anamux (AnalogMux instance)
# - ads1, ads2 (ADS1115 ADC instances)
# - digexp1, digexp2 (TCA9535 digital expander instances)

# Example usage:
powcon.enable_5v(True)  # Enable 5V power rail
voltage = ads1.raw_to_v(ads1.read(6, 0))  # Read ADC channel 0
print(f"ADC voltage: {voltage}V")
```

### First-Time Setup

For a fresh device, use the install command to set up required MicroPython packages:

```bash
cd picon
./run install  # Install dependencies and upload code
```
