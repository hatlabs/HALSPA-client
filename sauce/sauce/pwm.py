from contextlib import contextmanager

from machine import PWM, Pin


@contextmanager
def pwm_context_manager(gpio_number, freq, duty_u16):
    """
    Context manager for PWM.
    """
    pin = Pin(gpio_number, Pin.OUT)
    pwm = PWM(pin, freq=freq, duty_u16=duty_u16)
    try:
        yield pwm
    finally:
        pwm.deinit()
        pin.init(Pin.IN)
