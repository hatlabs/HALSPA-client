import time
from typing import Any, Dict, Optional

import serial
from loguru import logger

# Protocol constants
RAW_PASTE_COMMAND = b"\x05A\x01"
RAW_PASTE_SUPPORTED = b"R\x01"
RAW_PASTE_NOT_SUPPORTED = b"R\x00"
CHUNK_SIZE = 32  # Bytes to send per chunk in regular raw mode
MAX_RESPONSE_SIZE = 100000  # 100KB safety limit
EXECUTION_TIMEOUT_MULTIPLIER = 10

# Raspberry Pi Pico USB identifiers
PICO_VID = 0x2E8A
PICO_PIDS = [0x000A, 0x0005]


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
        if self.serial:
            try:
                if self.serial.is_open:
                    self.serial.close()
            except Exception:
                # Ignore errors during disconnection
                pass
            finally:
                self.serial = None
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

        Raises:
            ValueError: If code is empty or None.
            ConnectionError: If not connected to device.
            RuntimeError: If code execution fails.
            TimeoutError: If execution times out.
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        if not self._is_connected:
            self.connect()

        assert self.serial is not None, "Serial connection is not established"

        # Prepare the code (ensure it ends with newline)
        code = code.rstrip() + "\n"
        code_bytes = code.encode("utf-8")

        # Enter raw REPL mode first
        self._enter_raw_repl()

        # Set timeout if specified
        old_timeout = None
        if timeout is not None:
            old_timeout = self.serial.timeout
            self.serial.timeout = timeout

        try:
            # Try to enter raw paste mode first
            try:
                self._enter_raw_paste_mode()
                return self._execute_raw_paste(code_bytes)
            except RuntimeError:
                # Fall back to regular raw mode
                return self._execute_raw_mode(code_bytes)

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
            if (port.vid == PICO_VID and port.pid in PICO_PIDS) or (
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
            self._read_until(b">>>", timeout=5.0)
        except TimeoutError:
            # If we can't get back to normal REPL, try a more aggressive reset
            logger.warning("Could not exit raw REPL normally, performing hard reset")
            self._hard_reset_repl()

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
            start_time = time.time()
            while not result.endswith(term):
                char = self.serial.read(1)
                if not char:
                    elapsed = time.time() - start_time
                    current_timeout = (
                        timeout if timeout is not None else self.serial.timeout
                    )
                    raise TimeoutError(
                        f"Timeout ({elapsed:.1f}s, limit: {current_timeout}s) waiting for {term!r}, got {result!r}"
                    )
                result += char

                # Safety check to prevent infinite loops with very long responses
                if len(result) > MAX_RESPONSE_SIZE:
                    raise RuntimeError(f"Response too long while waiting for {term!r}")

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
        self.serial.write(RAW_PASTE_COMMAND)

        # Read the response to determine if raw paste mode is supported
        response = self.serial.read(2)

        if response == RAW_PASTE_SUPPORTED:
            # Device supports raw paste and has entered this mode
            # Read the window size increment (16-bit little endian)
            window_bytes = self.serial.read(2)
            self.paste_window_size = window_bytes[0] | (window_bytes[1] << 8)
            self.paste_remaining_window = self.paste_window_size
            return
        elif response == RAW_PASTE_NOT_SUPPORTED:
            # Device understands the command but doesn't support raw paste
            raise RuntimeError(
                "Device understands raw paste command but doesn't support it"
            )
        else:
            # Device doesn't understand raw paste command
            # Read and discard the rest of the response
            self._read_until(b">")
            raise RuntimeError(
                f"Device doesn't understand raw paste command, got: {response!r}"
            )

    def _execute_raw_paste(self, code_bytes: bytes) -> str:
        """Execute code using raw paste mode."""
        assert self.serial is not None, "Serial connection is not established"

        # Send the code in chunks using the window size provided by the device
        pos = 0
        while pos < len(code_bytes):
            # Check for flow control if window is empty OR if data is waiting
            if self.paste_remaining_window == 0 or self.serial.in_waiting:
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
                    raise RuntimeError(f"Unexpected character during raw paste: {char}")

            # Calculate how much we can send (must be > 0 at this point)
            chunk_size = min(len(code_bytes) - pos, self.paste_remaining_window)

            # Send a chunk of code
            chunk = code_bytes[pos : pos + chunk_size]
            self.serial.write(chunk)
            pos += chunk_size
            self.paste_remaining_window -= chunk_size

        # End the transmission
        self.serial.write(b"\x04")

        # Read confirmation EOT - device has received all data and is compiling
        char = self.serial.read(1)
        if char != b"\x04":
            if not char:
                raise TimeoutError("Timeout waiting for compilation confirmation")
            raise RuntimeError(f"Unexpected character after raw paste: {char}")

        # Read response - according to the MicroPython docs and pyboard.py reference,
        # there are two sections: output and error, both terminated by EOT
        return self._read_execution_result()

    def _execute_raw_mode(self, code_bytes: bytes) -> str:
        """Execute code using regular raw mode (like pyboard.py reference implementation)."""
        assert self.serial is not None, "Serial connection is not established"

        # Check we have a prompt
        data = self._read_until(b">")
        if not data.endswith(b">"):
            raise RuntimeError("Could not enter raw repl")

        # Write command in 32-byte chunks (like pyboard.py)
        for i in range(0, len(code_bytes), CHUNK_SIZE):
            chunk = code_bytes[i : min(i + CHUNK_SIZE, len(code_bytes))]
            self.serial.write(chunk)
            time.sleep(0.01)  # Small delay between chunks

        self.serial.write(b"\x04")  # End of input

        # Check if we could exec command
        data = self.serial.read(2)
        if data != b"OK":
            raise RuntimeError(f"Could not exec command, got: {data!r}")

        # Read execution result
        return self._read_execution_result()

    def _read_execution_result(self) -> str:
        """Read the result of code execution (works for both raw paste and raw mode)."""
        assert self.serial is not None, "Serial connection is not established"

        # Read normal output (until first EOT)
        output_data = self._read_until(
            b"\x04", timeout=max(30.0, self.timeout * EXECUTION_TIMEOUT_MULTIPLIER)
        )
        if not output_data.endswith(b"\x04"):
            raise TimeoutError("Timeout waiting for output EOF")
        output_data = output_data[:-1]  # Remove the EOT

        # Read error output (until second EOT)
        error_data = self._read_until(b"\x04", timeout=5.0)
        if not error_data.endswith(b"\x04"):
            raise TimeoutError("Timeout waiting for error EOF")
        error_data = error_data[:-1]  # Remove the EOT

        # Convert to strings and normalize line endings
        output = output_data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        error = (
            error_data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            if error_data
            else ""
        )

        if error:
            raise RuntimeError(f"Error executing code: {error}")

        return output

    def _hard_reset_repl(self) -> None:
        """Perform a hard reset when normal methods fail."""
        assert self.serial is not None, "Serial connection is not established"

        # Clear all buffers
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        # Try multiple interrupt sequences
        for _ in range(5):
            self.serial.write(b"\x03")  # Ctrl+C
            time.sleep(0.1)

        # Try to exit raw REPL if we're still in it
        self.serial.write(b"\x02")  # Ctrl+B
        time.sleep(0.2)

        # Send Ctrl+D for soft reset
        self.serial.write(b"\x04")
        time.sleep(0.5)

        # Clear buffers again
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        # Try to get to a clean state - read whatever is there with a short timeout
        try:
            # Set a very short timeout to quickly consume any remaining output
            old_timeout = self.serial.timeout
            self.serial.timeout = 0.1

            # Read and discard whatever is in the buffer
            while True:
                data = self.serial.read(100)
                if not data:
                    break

        except Exception:
            pass  # Ignore any errors during cleanup
        finally:
            # Restore original timeout
            self.serial.timeout = old_timeout
