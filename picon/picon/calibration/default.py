"""
Default HALSPA calibration values

These are safe fallback values used when no custom calibration is available.
For production use, copy custom_template.py to custom.py and update with measured values.
"""

# Board identification
BOARD_ID = "UNCALIBRATED"
CALIBRATION_DATE = "N/A"
CALIBRATED_BY = "factory"

# ADC1 channel gain factors
ADC1_CH0_GAIN = 1.0      # Current sense amp 1 (A/V)
ADC1_CH1_GAIN = 1.0      # Programmable voltage output  
ADC1_CH2_GAIN = 1.0      # 12V supply voltage divider
ADC1_CH3_GAIN = 1.0      # 5V supply voltage divider

# ADC2 channels
ADC2_CH0_GAIN = 1.0
ADC2_CH1_GAIN = 1.0  
ADC2_CH2_GAIN = 1.0
ADC2_CH3_GAIN = 1.0

# Multi-channel arrays (for convenience)
ADC1_GAINS = [ADC1_CH0_GAIN, ADC1_CH1_GAIN, ADC1_CH2_GAIN, ADC1_CH3_GAIN]
ADC2_GAINS = [ADC2_CH0_GAIN, ADC2_CH1_GAIN, ADC2_CH2_GAIN, ADC2_CH3_GAIN]

# Voltage divider ratios
VOLTAGE_DIV_12V = 1.0     # 12V supply voltage divider ratio
VOLTAGE_DIV_5V = 1.0      # 5V supply voltage divider ratio

# Current limits (Amps)
CURRENT_LIMIT_12V_1 = 2.5
CURRENT_LIMIT_12V_2 = 2.5
CURRENT_LIMIT_5V = 3.0
CURRENT_LIMIT_3V3 = 2.0