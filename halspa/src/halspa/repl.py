import time
from typing import Any, Dict, Optional

import serial
from loguru import logger


class REPL:
    """
    Client for communicating with a MicroPython device.
    Handles connection, code execution, and response parsing.
    """

    def __init__(
        self, port: str | None = None, baudrate: int = 115200, timeout: float = 1.0
    ):
        """
        Initialize the REPL client.

        Args:
            port: Serial port to connect to. If None, will attempt auto-detection.
            baudrate: Baud rate for the serial connection.
            timeout: Serial timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: serial.Serial | None = None
        self._is_connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self) -> bool:
        """
        Connect to the HALSPA device.

        Returns:
            True if connection successful, False otherwise.
        """
        if self._is_connected:
            return True

        # Auto-detect port if not specified
        if not self.port:
            self.port = self._auto_detect_port()
            if not self.port:
                raise ConnectionError("Could not auto-detect HALSPA device")

        logger.debug(f"Connecting to HALSPA device on port {self.port}")

        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

            # Reset the device and get to a clean REPL
            self._reset_repl()
            self._is_connected = True
            return True

        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to HALSPA device: {e}")

    def disconnect(self) -> None:
        """Close the connection to the HALSPA device."""
        if self.serial and self.serial.is_open:
            self.serial.close()
        self._is_connected = False

    def reset(self) -> None:
        """Reset the REPL to a clean state."""
        if not self._is_connected:
            raise ConnectionError("Not connected to HALSPA device")
        self._reset_repl()

    def execute(self, code: str, timeout: float | None = None) -> str:
        """
        Execute code using raw paste mode for better performance with larger code blocks.

        Args:
            code: Python code to execute.
            timeout: Optional timeout override for this operation.

        Returns:
            The output of the executed code.
        """
        if not self._is_connected:
            self.connect()

        assert self.serial is not None, "Serial connection is not established"

        # Prepare the code (ensure it ends with newline)
        logger.debug(f"Executing code: {code.strip()}")
        code = code.rstrip() + "\r\n"

        code_bytes = code.encode("utf-8")

        # Enter raw REPL mode first
        self._enter_raw_repl()

        # Set timeout if specified
        old_timeout = None
        if timeout is not None:
            old_timeout = self.serial.timeout
            self.serial.timeout = timeout

        try:
            # Try to enter raw paste mode
            self._enter_raw_paste_mode()
            # Raises a RuntimeError if raw paste mode is not supported

            # Send the code in chunks using the window size provided by the device
            pos = 0
            while pos < len(code_bytes):
                # Calculate how much we can send
                chunk_size = min(len(code_bytes) - pos, self.paste_remaining_window)
                if chunk_size == 0:
                    # Wait for flow control byte
                    char = self.serial.read(1)
                    if char == b"\x01":
                        # Window size has been incremented
                        self.paste_remaining_window = self.paste_window_size
                        continue
                    elif char == b"\x04":
                        # Device wants to end transmission
                        self.serial.write(b"\x04")
                        break
                    elif not char:
                        raise TimeoutError("Timeout during raw paste transmission")
                    else:
                        raise RuntimeError(
                            f"Unexpected character during raw paste: {char}"
                        )

                # Send a chunk of code
                chunk = code_bytes[pos : pos + chunk_size]
                self.serial.write(chunk)
                pos += chunk_size
                self.paste_remaining_window -= chunk_size

                # Check if there's a flow control byte waiting
                if self.serial.in_waiting:
                    char = self.serial.read(1)
                    if char == b"\x01":
                        # Window size has been incremented
                        self.paste_remaining_window = self.paste_window_size
                    elif char == b"\x04":
                        # Device wants to end transmission
                        self.serial.write(b"\x04")
                        break
                    else:
                        raise RuntimeError(
                            f"Unexpected character during raw paste: {char}"
                        )

            # End the transmission
            self.serial.write(b"\x04")

            # Read a single byte. It should be the EOT (end of transmission) character
            char = self.serial.read(1)
            if char != b"\x04":
                raise RuntimeError(f"Unexpected character after raw paste: {char}")

            # Read response, handling output and errors as in execute()
            output_bytes = bytearray()
            error_bytes = bytearray()

            # Read until first EOT (end of output)
            while True:
                char = self.serial.read(1)
                if not char:
                    raise TimeoutError("Timeout waiting for output")
                if char == b"\x04":  # EOT marker
                    break
                output_bytes.extend(char)

            # Check if there's an error (another EOT will follow)
            is_error = False
            while True:
                char = self.serial.read(1)
                if not char:
                    # If we timeout here, it means there was no error
                    break

                if char == b"\x04":  # Second EOT marker (end of error)
                    break

                is_error = True
                error_bytes.extend(char)

            # Wait for the prompt to return
            self._read_until(b">")

            # Convert to strings
            output = output_bytes.decode("utf-8")
            error = error_bytes.decode("utf-8") if is_error else ""

            if error:
                # If there's an error, raise an exception
                raise RuntimeError(f"Error executing code: {error}")

            return output

        finally:
            # Restore timeout if changed
            if old_timeout is not None:
                self.serial.timeout = old_timeout

            # Exit raw REPL mode
            self._exit_raw_repl()

    def call_function(self, func_name: str, *args, **kwargs) -> Any:
        """
        Call a function on the device with the given arguments.

        Args:
            func_name: Name of the function to call.
            *args: Positional arguments to pass.
            **kwargs: Keyword arguments to pass.

        Returns:
            Result of the function call, converted to Python types.

        Raises:
            RuntimeError: If the function execution fails on the device.
        """
        # Format the arguments
        args_strs = [repr(arg) for arg in args]
        kwargs_strs = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        all_args = ", ".join(args_strs + kwargs_strs)

        # Build and execute the code
        code = f"print(repr({func_name}({all_args})))"
        output = self.execute(code)

        # Evaluate the result
        try:
            return eval(output.strip())
        except (SyntaxError, ValueError):
            # If the result can't be evaluated (e.g., it's not a valid Python literal),
            # just return the string
            return output.strip()

    def import_module(self, module_name: str) -> None:
        """
        Import a module on the device.

        Args:
            module_name: Name of the module to import.
        """
        self.execute(f"import {module_name}")

    def get_device_info(self) -> Dict[str, str]:
        """
        Get basic information about the connected device.

        Returns:
            Dictionary with device information.
        """
        info = {}

        # Get MicroPython version
        info["micropython"] = self.execute("import os; print(os.uname().version)")

        # Get machine info
        info["machine"] = self.execute("import os; print(os.uname().machine)")

        # Get available modules
        info["modules"] = self.execute(
            "import sys; print([m for m in sys.modules.keys() if not m.startswith('_')])"
        )

        return info

    def set_pin_mode(self, pin: int, mode: str) -> None:
        """
        Set the mode of a GPIO pin.

        Args:
            pin: GPIO pin number (0-39)
            mode: Pin mode ("input", "output", "pullup", "pulldown")
        """
        if not 0 <= pin <= 39:
            raise ValueError(f"Pin must be 0-39, got {pin}")

        if mode not in ["input", "output", "pullup", "pulldown"]:
            raise ValueError(f"Invalid pin mode: {mode}")

        self.execute(f"from machine import Pin; Pin({pin}).mode('{mode}')")

    # Private helper methods

    def _auto_detect_port(self) -> Optional[str]:
        """
        Attempt to auto-detect the serial port for the HALSPA device.

        Returns:
            Port name if found, None otherwise.
        """
        import serial.tools.list_ports

        # Look for Raspberry Pi Pico or compatible USB devices
        for port in serial.tools.list_ports.comports():
            # Check for Pico's USB VID:PID
            if (port.vid == 0x2E8A and port.pid in [0x000A, 0x0005]) or (
                "Pico" in port.description and "Debugprobe" not in port.description
            ):
                return port.device

        return None

    def _reset_repl(self) -> None:
        """Reset the REPL to ensure we're in a clean state."""
        assert self.serial is not None, "Serial connection is not established"
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        # Send Ctrl+C a few times to interrupt any running program
        for _ in range(3):
            self.serial.write(b"\x03")
            time.sleep(0.1)

        # Wait for the prompt
        self._read_until(b">>>")

        # Send Ctrl+D to reset the REPL
        self.serial.write(b"\x04")
        time.sleep(0.1)
        # Clear the input buffer
        self.serial.reset_input_buffer()

    def _enter_raw_repl(self) -> None:
        """
        Enter raw REPL mode.

        Raises:
            ConnectionError: If cannot enter raw REPL mode.
        """
        assert self.serial is not None, "Serial connection is not established"

        # Send Ctrl+C to stop any running program
        self.serial.write(b"\x03")
        time.sleep(0.1)

        # Flush input buffer
        self.serial.reset_input_buffer()

        # Send Ctrl+A to enter raw REPL
        self.serial.write(b"\x01")

        # Try to read the raw REPL intro text
        try:
            response = self._read_until(b"raw REPL; CTRL-B to exit\r\n>", timeout=2.0)
            if not response.endswith(b"raw REPL; CTRL-B to exit\r\n>"):
                raise ConnectionError("Failed to enter raw REPL mode")
        except TimeoutError:
            raise ConnectionError("Timeout waiting for raw REPL mode")

    def _exit_raw_repl(self) -> None:
        """Exit raw REPL mode."""
        assert self.serial is not None, "Serial connection is not established"

        # Send Ctrl+B to exit raw REPL
        self.serial.write(b"\x02")

        # Try to read until we see the normal REPL prompt
        try:
            self._read_until(b">>>", timeout=2.0)
        except TimeoutError:
            # If we can't get back to normal REPL, try to reset
            self._reset_repl()

    def _read_until(self, term: bytes, timeout: float | None = None) -> bytes:
        """
        Read from serial until a terminator sequence is found.

        Args:
            term: Terminator sequence
            timeout: Optional timeout override

        Returns:
            Bytes read from serial, including the terminator
        """
        assert self.serial is not None, "Serial connection is not established"
        old_timeout = None
        if timeout is not None:
            old_timeout = self.serial.timeout
            self.serial.timeout = timeout

        try:
            result = b""
            while not result.endswith(term):
                char = self.serial.read(1)
                if not char:
                    raise TimeoutError("Timeout waiting for response")
                result += char
            return result
        finally:
            if old_timeout is not None:
                self.serial.timeout = old_timeout

    def _enter_raw_paste_mode(self) -> None:
        """
        Enter raw paste mode.

        Returns:
            None
        """
        assert self.serial is not None, "Serial connection is not established"
        # Send raw paste mode command sequence
        self.serial.write(b"\x05A\x01")

        # Read the response to determine if raw paste mode is supported
        response = self.serial.read(2)

        if response == b"R\x01":
            # Device supports raw paste and has entered this mode
            # Read the window size increment (16-bit little endian)
            window_bytes = self.serial.read(2)
            self.paste_window_size = window_bytes[0] | (window_bytes[1] << 8)
            self.paste_remaining_window = self.paste_window_size
            return
        elif response == b"R\x00":
            # Device understands the command but doesn't support raw paste
            raise RuntimeError(
                "Device understands raw paste command but doesn't support it"
            )
        else:
            # Device doesn't understand raw paste command
            # Read and discard the rest of the response
            self._read_until(b">")
            raise RuntimeError("Device doesn't understand raw paste command")
