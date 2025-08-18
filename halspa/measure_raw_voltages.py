#!/usr/bin/env python3
"""
Script to measure and print raw (uncalibrated) voltages from all ADC channels.
Uses the read_uncalibrated_voltage() method to show actual voltages at ADC inputs.

This module can be imported to use the measurement functions in custom scripts.
"""

import sys
from typing import Optional

from halspa.adc import ADS1115, measure_all_channels, print_measurements
from halspa.repl import REPL


def connect_to_halspa() -> Optional[REPL]:
    """
    Connect to HALSPA device and return REPL instance.
    
    Returns:
        REPL instance if successful, None if connection failed
    """
    repl = REPL()
    try:
        repl.connect()
        print("Connected to HALSPA device")
        return repl
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None


def main():
    """Main script execution."""
    print("Raw ADC Voltage Measurement Script")
    print("=" * 40)
    print("This script shows uncalibrated voltages directly from the ADS1115 ADCs")
    print()

    # Connect to the REPL
    repl = connect_to_halspa()
    if not repl:
        return 1

    # Initialize ADS1115 instances
    ads1 = ADS1115(repl, 1, 1)
    ads2 = ADS1115(repl, 2, 1)

    print("\nMeasuring uncalibrated voltages...")
    print()

    # Measure all channels
    measurements = measure_all_channels(ads1, ads2)
    
    # Print results
    print_measurements(measurements)

    repl.disconnect()
    print("Measurement complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
