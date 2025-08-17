"""
HALSPA Calibration Package

Automatically imports calibration constants, preferring custom values
over defaults when available.

Usage:
    from picon.calibration import ADC1_CH0_SCALE, ADC1_SCALES
    
    # Direct constant access
    scale = ADC1_CH0_SCALE
    
    # Array access
    scale = ADC1_SCALES[0]  # Channel 0
"""

# Try to import from custom calibration first, fall back to defaults
try:
    from picon.calibration.custom import *
    print(f"Using custom calibration for board {BOARD_ID} (calibrated {CALIBRATION_DATE})")
except ImportError:
    from picon.calibration.default import *
    print("Using default calibration values (UNCALIBRATED)")