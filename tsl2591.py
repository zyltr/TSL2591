from machine import I2C
from micropython import const


class Gain:
    """
    Gain Constants
    """

    LOW: int = const(0x00)
    MEDIUM: int = const(0x10)
    HIGH: int = const(0x20)
    MAX: int = const(0x30)


class Time:
    """
    Integration Time Constants
    """

    MS100: int = const(0x00)
    MS200: int = const(0x01)
    MS300: int = const(0x02)
    MS400: int = const(0x03)
    MS500: int = const(0x04)
    MS600: int = const(0x05)


class TSL2591:
    """
    TSL2591 High-Precision Light Sensor
    """

    ADDRESS: int = const(0x29)

    COMMAND: int = const(0xA0)
    DEVICE_ID = const(0x50)
    LUX_COEFB = 1.64
    LUX_COEFC = 0.59
    LUX_COEFD = 0.86
    LUX_DF = 408.0
    MAX_COUNT_100MS = const(36863)
    MAX_COUNT = const(65535)
    REGISTER_ENABLE: int = const(0x00)
    REGISTER_CONFIG: int = const(0x01)
    REGISTER_ID: int = const(0x12)
    REGISTER_C0DATAL: int = const(0x14)
    REGISTER_C0DATAH: int = const(0x15)
    REGISTER_C1DATAL: int = const(0x16)
    REGISTER_C1DATAH: int = const(0x17)

    def __init__(
        self, device: I2C, address: int = ADDRESS, debug: bool = False
    ) -> None:
        """
        :param device: The I2C interface instance used to communicate with the device.
        :param address: The I2C address of the TSL2591 sensor. Defaults to ADDRESS 0x29.
        :param debug: If True, enables debug mode to output additional logs. Defaults to False.
        """
        self._address = address
        self._debug = debug
        self._device = device
        self._gain = Gain.LOW
        self._time = Time.MS100

        # Verify Device ID
        if self._debug:
            print("Checking ID...")
        self._target(TSL2591.REGISTER_ID)
        value: int = int.from_bytes(self._read())
        if value != TSL2591.DEVICE_ID:
            raise RuntimeError("Failed to find TSL2591!")

        # Enable
        self.enable()

    def _print(self, message: str, value: bytes) -> None:
        """
        :param message: String message to be displayed alongside the debug information.
        :param value: Byte object representing the value to be printed in various formats.
        :return: None
        """
        if self._debug:
            conversion = int.from_bytes(value)
            print(
                f"{message}: Bytes {value} | Hex {value.hex()} | Dec {conversion} | Bin {bin(conversion)}"
            )

    def _target(self, register: int) -> None:
        """
        :param register: The register address to which the command is targeted, specified as an integer.
        :return: None
        """
        buffer: bytes = (TSL2591.COMMAND | register).to_bytes()
        self._print(message="Command", value=buffer)
        self._device.writeto(self._address, buffer)

    def _read(self, nbytes: int = 1) -> bytes:
        """
        Reads a specific number of bytes from a device.

        :param nbytes: The number of bytes to read from the device. Defaults to 1.
        :return: The bytes read from the device.
        """
        reading: bytes = self._device.readfrom(self._address, nbytes)
        self._print(message="Reading", value=reading)
        return reading

    def _write(self, buffer: bytes) -> None:
        """
        :param buffer: The byte buffer containing the data to be written to the device.
        :return: None
        """
        self._print(message="Writing", value=buffer)
        self._device.writeto(self._address, buffer)

    def enable(
        self,
        aen: bool = True,
        aien: bool = False,
        npien: bool = False,
        pon: bool = True,
    ) -> None:
        """
        :param aen: Enable or disable ALS. Set to True to enable, False to disable.
        :param aien: Enable or disable the ALS interrupt. Set to True to enable, False to disable.
        :param npien: Enable or disable the No Persist interrupt. Set to True to enable, False to disable.
        :param pon: Power ON or OFF the sensor. Set to True to power on, False to power off.
        :return: None
        """
        if self._debug:
            print(f"{'Enabling' if pon else 'Disabling'} TSL2591...")
            print(f"AEN: {aen}, AIEN: {aien}, NPIEN: {npien}, PON: {pon}")
        self._target(TSL2591.REGISTER_ENABLE)
        buffer: bytes = (npien << 7 | aien << 4 | aen << 1 | pon).to_bytes()
        self._write(buffer)

    def disable(self) -> None:
        """
        Disables the current object by setting configurations for attributes to False.

        :return: None
        """
        self.enable(aen=False, pon=False)

    @property
    def full_spectrum(self) -> int:
        """
        :return: Full spectrum luminosity value.
        """
        C0, C1 = self.raw_luminosity
        return C1 << 16 | C0

    @property
    def gain(self) -> int:
        """
        :return: The value of the gain property as an integer.
        """
        return self._gain

    @gain.setter
    def gain(self, value: int) -> None:
        """
        :param value: The gain value to set for the device. Must be one of the predefined constants (Gain.LOW, Gain.MEDIUM, Gain.HIGH, Gain.MAX).
        :return: None
        """
        if self._debug:
            print("Setting Gain...")
        assert value in (Gain.LOW, Gain.MEDIUM, Gain.HIGH, Gain.MAX)
        self._target(TSL2591.REGISTER_CONFIG)
        buffer: bytes = self._read()
        reading: int = int.from_bytes(buffer)
        CONFIG_CLEAR_AGAIN_MASK: int = 0x07
        reading &= CONFIG_CLEAR_AGAIN_MASK
        reading |= value
        self._write(reading.to_bytes())
        self._gain = value

    @property
    def infrared(self) -> int:
        """
        :return: Infrared luminosity value.
        """
        _, C1 = self.raw_luminosity
        return C1

    @property
    def lux(self) -> float:
        """
        Calculates lux based on the current gain and integration time. Can raise an error is the sensor becomes
        over-saturated. This can happen when the environment is too bright for the sensor, and therefore, gain and
        integration time must be adjusted accordingly.

        :return: The calculated lux value as a floating-point number.
                 Raises RuntimeError if sensor readings exceed the maximum count for the current time setting.
        """
        C0, C1 = self.raw_luminosity

        timings: dict = {
            Time.MS100: 0.1,
            Time.MS200: 0.2,
            Time.MS300: 0.3,
            Time.MS400: 0.4,
            Time.MS500: 0.5,
            Time.MS600: 0.6,
        }

        atime: float = timings[self._time] * 1000
        counts: int = (
            TSL2591.MAX_COUNT_100MS if self._time == Time.MS100 else TSL2591.MAX_COUNT
        )

        if C0 >= counts or C1 >= counts:
            raise RuntimeError("Overflow reading channels! Try reducing sensor gain!")

        again = 1.0

        if self._gain == Gain.MEDIUM:
            again = 25.0
        elif self._gain == Gain.HIGH:
            again = 428.0
        elif self._gain == Gain.HIGH:
            again = 9876.0

        CPL = (atime * again) / TSL2591.LUX_DF
        LUX0 = (C0 - (TSL2591.LUX_COEFB * C1)) / CPL
        LUX1 = ((TSL2591.LUX_COEFC * C0) - (TSL2591.LUX_COEFD * C1)) / CPL

        return max(LUX0, LUX1)

    @property
    def raw_luminosity(self) -> tuple[int, int]:
        """
        :return: A tuple containing two integers.
                 The first integer represents the raw luminosity data from channel 0,
                 and the second integer represents the raw luminosity data from channel 1.
        """
        self._target(TSL2591.REGISTER_C0DATAL)
        C0L: bytes = self._read()
        self._target(TSL2591.REGISTER_C0DATAH)
        C0H: bytes = self._read()
        self._target(TSL2591.REGISTER_C1DATAL)
        C1L: bytes = self._read()
        self._target(TSL2591.REGISTER_C1DATAH)
        C1H: bytes = self._read()

        C0 = C0H + C0L
        C1 = C1H + C1L

        return int.from_bytes(C0), int.from_bytes(C1)

    @property
    def visible(self) -> int:
        """
        Calculates the visible light.

        :return: Visible light component as an integer
        """
        _, C1 = self.raw_luminosity
        return self.full_spectrum - C1

    @property
    def time(self) -> int:
        """
        :return: The current value of the integration time attribute.
        """
        return self._time

    @time.setter
    def time(self, value: Time) -> None:
        """
        Sets the integration time of the sensor. This method ensures that the provided value is one of the
        predefined acceptable constants for time intervals.

        :param value: Desired integration time. Must be one of the predefined
                      constants (Time.MS100, Time.MS200, Time.MS300, Time.MS400, Time.MS500, Time.MS600).
        :return: None
        """
        if self._debug:
            print("Setting Integration Time...")

        self._target(TSL2591.REGISTER_CONFIG)
        buffer: bytes = self._read()
        reading: int = int.from_bytes(buffer)
        CONFIG_CLEAR_TIME_MASK: int = 0x30
        reading &= CONFIG_CLEAR_TIME_MASK
        reading |= value
        self._write(reading.to_bytes())
        self._time = value
