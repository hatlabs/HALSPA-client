# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HALSPA Kettle is a Python library for orchestrating the HALSPA test jig, a hardware testing interface that sits between bed-of-nails test fixtures and a Raspberry Pi. The system consists of two main components:

1. **Client Library** (`halspa/` directory) - Python library that runs on Raspberry Pi using PyTest
2. **Device Firmware** (`picon/` directory) - MicroPython library running on Raspberry Pi Pico 2

## Architecture

The system uses a client-server architecture where the Raspberry Pi (client) sends MicroPython code snippets to the Pico 2 (server) via REPL protocol over USB serial:

- **REPL Communication**: `halspa/src/halspa/repl.py` handles all MicroPython REPL protocol communication
- **Hardware Abstraction**: Each hardware subsystem has a corresponding Python class that sends commands to the Pico
- **Test Framework**: Uses PyTest with fixtures for hardware testing

### Key Components

- **Power Control**: `PowerControl` class manages power rails (5V, 3.3V, 12V current limiters)
- **ADC Interface**: `ADS1115` and `ADCChannel` classes for analog-to-digital conversion
- **Digital I/O**: `TCA9535` digital expander and `Pin` classes for GPIO control
- **Analog Multiplexing**: `AnalogMux` class for switching analog signals
- **Device Communication**: `REPL` class implements MicroPython raw paste mode protocol

## Development Commands

### Testing
```bash
cd halspa
pytest                           # Run all tests
pytest tests/self/self_test.py   # Run hardware self-tests
pytest -v                       # Verbose test output
```

### Python Environment
```bash
cd halspa
uv sync                         # Install dependencies using uv
uv run pytest                  # Run tests in virtual environment
```

### Hardware Connection
Tests require a physical HALSPA board connected via USB. The system auto-detects Raspberry Pi Pico 2 devices with VID:PID `2E8A:000A` or `2E8A:0005`.

## Development Patterns

### Hardware Class Structure
All hardware control classes follow this pattern:
1. Take a `REPL` instance in `__init__`
2. Execute MicroPython import/setup code during initialization
3. Provide Python methods that send commands via `repl.execute()`
4. Use `textwrap.dedent()` for multi-line MicroPython code blocks

### Testing with Fixtures
Hardware tests use PyTest fixtures that:
- Establish REPL connection once per test module
- Initialize hardware control objects
- Ensure proper cleanup after tests

### Error Handling
- REPL protocol includes timeout and error detection
- Hardware faults are read via power control status registers  
- Connection auto-detection with fallback to manual port specification

## Hardware Subsystems

The HALSPA board includes:
- DUT power outputs (5V, 3.3V)
- Current limiters with fault detection
- Current sense amplifiers
- Programmable voltage sources (0-12V via PWM + opamps)
- Dual 4-channel ADCs (ADS1115)
- 4x 8-to-1 analog multiplexers
- Digital expanders (TCA9535)
- Level shifters and GPIO

Each subsystem has corresponding Python control classes in `halspa/src/halspa/` and MicroPython implementations in `picon/picon/`.