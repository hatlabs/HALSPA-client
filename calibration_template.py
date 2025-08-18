"""
HALSPA Board Custom Calibration Template

Copy this file to custom_calibration.py in the same directory.
Go through the new file and follow the instructions to calibrate your board.

To upload your changes on the HALSPA pico, run `./run upload_calibration`.
"""

#######################################################################
# Board identification

BOARD_ID = "HALSPA-001"  # Update with actual board serial
CALIBRATION_DATE = "2025-01-15"  # Date of calibration
CALIBRATED_BY = "John Doe"  # Name of person who calibrated

#######################################################################
# Current limits for 12V Limit 1 and 2
#
# 12V current limiters have a latching current limiter that cuts the output
# if the current exceeds a certain threshold. The threshold is set by the
# 0-100 kOhm trimmer potentiometer on the board.
#
# Calibration Process: Measure the voltage between the test pads
# and set below. The current limit is I_lim = 2.0 A/V * V_measured.

# The values below are informational only; the actual current limiting is done
# in the hardware.


def _calc_12v_lim(v_measured: float) -> float:
    return 2.0 * v_measured  # 2.0 A/V


CURRENT_LIMIT_12V_1 = _calc_12v_lim(v_measured=1.0)  # Measure and update
CURRENT_LIMIT_12V_2 = _calc_12v_lim(v_measured=1.0)  # Measure and update

#######################################################################
# Current limits for 3.3-5V Limit 1-4
#
# The 3.3-5V current limiters are implemented using AP22652A current limiters.
# They have a programmable current limit set by a 200 kOhm trimmer potentiometer
# connected to the AP22652A's ILIM pin.
#
# Calibration Process: Measure the resistance between the test pads
# and set here. The resistance defines the current limit of AP22652A as described
# in the datasheet page 10: https://jlcpcb.com/api/file/downloadByFileSystemAccessId/8560085854287642624.
# The formula is: I_lim = 30321 / (R_measured / 1000.0)**1.055

# The values below are informational only; the actual current limiting is done
# in the hardware.


def _calc_3v3_curlim(r_meas: float) -> float:
    return 30321 / (r_meas / 1000.0) ** 1.055


CURRENT_LIMIT_3V3_1 = _calc_3v3_curlim(r_meas=50.0)  # Measure and update
CURRENT_LIMIT_3V3_2 = _calc_3v3_curlim(r_meas=50.0)  # Measure and update
CURRENT_LIMIT_3V3_3 = _calc_3v3_curlim(r_meas=50.0)  # Measure and update
CURRENT_LIMIT_3V3_4 = _calc_3v3_curlim(r_meas=50.0)  # Measure and update

#######################################################################
# Op-amp 1-4 gain calibration
#
# Onboard op-amps can be used to create PWM controlled voltage outputs.
#
# The gain is set by a trimmer potentiometer controlling the non-inverting
# feedback loop. The gain is calculated as:
# Gain = 1 + RF / R2
# where RF is the feedback resistor and R2 is the ground resistor.
#
# Calibration Process:
# 1. Measure RF between the F and 2 test pads.
# 2. Measure R2 between the 2 and GND test pads.
# 3. Validate that RF + R2 is approximately 200 kOhm.


def _calc_opamp_gain(rf: float, r2: float) -> float:
    return 1 + (rf / r2)  # Gain calculation based on resistors


OPAMP_GAIN_1 = _calc_opamp_gain(rf=50e3, r2=50e3)  # Update with measured values
OPAMP_GAIN_2 = _calc_opamp_gain(rf=50e3, r2=50e3)  # Update with measured values
OPAMP_GAIN_3 = _calc_opamp_gain(rf=50e3, r2=50e3)  # Update with measured values
OPAMP_GAIN_4 = _calc_opamp_gain(rf=50e3, r2=50e3)  # Update with measured values


########################################################################
# ADC input gain calibration
#
# The ADS1115 ADC channel input gain must be adjusted to limit the maximum
# input voltage to 3.3V. The gain is set by adjusting the trimmer potentiometer
# of each channel. The input pots define voltage dividers that scale
# the input voltages.
#
# The gain is calculated as:
# Gain = Rb / Rbt
#
# where Rb is the voltage divider bottom resistor and Rbt is the voltage divider
# total resistance.
#
# Calibration Process (alternative 1):
# 1. Measure Rb between the G and middle test pads
# 2. Measure Rbt between the G and T test pads.
# 3. Validate that Rbt is approximately 100 kOhm.
#
# Calibration Process (alternative 2):
# 1. Connect a known voltage (e.g. 1.0V) to the ADC input.
# 2. Run the halspa/measure_raw_voltages.py script to measure the raw voltage.
# 3. Calculate the gain as Gain = V_measured / V_input, where V_measured is the
#    measured raw voltage and V_input is the known input voltage.


def _calc_adc_gain(rb: float, rbt: float) -> float:
    if rbt == 0:
        raise ValueError("Total resistance Rbt cannot be zero")
    return rb / rbt  # Gain calculation based on resistors


ADC1_CH0_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values
ADC1_CH1_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values
ADC1_CH2_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values
ADC1_CH3_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values

ADC2_CH0_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values
ADC2_CH1_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values
ADC2_CH2_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values
ADC2_CH3_GAIN = _calc_adc_gain(rb=50e3, rbt=100e3)  # Update with measured values

# Convenience arrays for programmatic access (required by ADC system)
ADC1_GAINS = [ADC1_CH0_GAIN, ADC1_CH1_GAIN, ADC1_CH2_GAIN, ADC1_CH3_GAIN]
ADC2_GAINS = [ADC2_CH0_GAIN, ADC2_CH1_GAIN, ADC2_CH2_GAIN, ADC2_CH3_GAIN]
