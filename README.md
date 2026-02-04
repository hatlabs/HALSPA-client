# HALSPA Client: Board Driver Library for HALSPA

## Background

HALSPA (Hat Labs Spaghetti Board) is a generic test jig interface board that sits between a bed-of-nails test fixture and a Raspberry Pi computer. It can be used for rapid development of test jigs for various digital and analog circuits.

The `halspa` Python library drives the HALSPA board directly over the Raspberry Pi's I2C bus using `smbus2`. It provides a `HalspaBoard` top-level object that owns the bus and exposes all on-board device drivers (ADCs, digital expanders, analog muxes, power control). Tests are written with PyTest.

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

## Quick Start

```bash
cd halspa
uv sync
uv run pytest
```
