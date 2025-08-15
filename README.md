# HALSPA Kettle: Testing Libraries for HALSPA: Hat Labs Spaghetti Board

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

## Kettle Introduction

HALSPA Kettle is a Python library for orchestrating the HALSPA test jig. It is designed to be used with the HALSPA hardware and provides interfaces implementing tests using PyTest. The tests interact with the `picon` MicroPython library running on the Raspberry Pi Pico 2. The tests are designed to be run on the Raspberry Pi using PyTest, which sends MicroPython snippets to the Pico 2 to run individual tests and register the test results.

It is also possible to connect the Raspberry Pi GPIO header directly to the HALSPA hardware. In this case, Raspberry Pi GPIO I/O can be used directly to interact with the HALSPA hardware.
