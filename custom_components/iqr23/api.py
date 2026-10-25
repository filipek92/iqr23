"""Async client for the iQ R23 heating controller web interface.

This module has no Home Assistant dependencies, so it can be tested and used standalone.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum

import aiohttp
import xmltodict

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)

# XML endpoints polled on every refresh; their contents are merged into one flat dict.
DATA_FILES = (
    "data",
    "data_i_all",
    "data_t_zas",
    "data_n_txo",
    "data_n_tix",
    "data_t_ek1",
    "data_t_ek2",
    "data_t_krb",
    "data_t_sol",
    "data_t_baz",
    "data_t_chl",
)

SAVE_BUTTON = 200
EMPTY_TEMPERATURES = {"--.-", "-.-", "--", "-"}


class IQR23Error(Exception):
    """Base error of the iQ R23 client."""


class IQR23ConnectionError(IQR23Error):
    """The controller could not be reached or returned invalid data."""


class IQR23AuthError(IQR23Error):
    """Login to the controller failed."""


class OutputMode(StrEnum):
    """Operating mode of a digital output."""

    AUTO = "auto"
    AUTO_R = "auto_r"
    ON = "on"
    OFF = "off"


@dataclass(frozen=True, slots=True)
class DigitalOutput:
    """Digital output of the controller.

    `key` is a stable identifier, `name` the label used by the controller.
    `state_key` holds the actual relay state, `mode_keys` map XML keys flagging the
    active mode, `mode_buttons` map modes to web UI buttons switching to them.
    """

    key: str
    name: str
    state_key: str
    mode_keys: dict[str, OutputMode]
    mode_buttons: dict[OutputMode, int]


def _output(name: str, index: int) -> DigitalOutput:
    """Build an output definition; the controller numbers them in fixed strides."""
    col = 400 + index * 5
    button = 300 + index * 4
    modes = (OutputMode.AUTO, OutputMode.AUTO_R, OutputMode.ON, OutputMode.OFF)
    return DigitalOutput(
        key=name.lower().replace("/", ""),
        name=name,
        state_key=f"col{col}",
        mode_keys={f"col{col + 1 + i}": mode for i, mode in enumerate(modes)},
        mode_buttons={mode: button + i for i, mode in enumerate(modes)},
    )


DIGITAL_OUTPUTS: dict[str, DigitalOutput] = {
    output.key: output
    for output in (
        _output(name, index)
        for index, name in enumerate(
            ("SP1", "SP2", "OVR", "KRB", "SOL", "TVC", "TO1", "TO2", "TCC", "T/C", "H/D", "STO")
        )
    )
}


@dataclass(frozen=True, slots=True)
class Setpoint:
    """Setting adjusted by the web UI -/+ buttons, one `step` per press.

    `file` is the XML file holding `value_key`. Presses beyond `min_value`..`max_value`
    are silently ignored by the controller. Some limits also follow other settings,
    e.g. a minimum stays below its maximum, so the full range is not always reachable.
    """

    key: str
    file: str
    value_key: str
    minus_button: int
    plus_button: int
    min_value: int
    max_value: int
    step: int = 1


# Limits measured on the controller (firmware iQR23L08b); coupled pairs list the outer bounds.
SETPOINTS: dict[str, Setpoint] = {
    setpoint.key: setpoint
    for setpoint in (
        Setpoint("tank_base", "data_t_zas", "txt503", 100, 101, 10, 85),
        Setpoint("tank_upper_spring", "data_t_zas", "txt510", 102, 103, 10, 80),
        Setpoint("tank_upper_summer", "data_t_zas", "txt511", 104, 105, 10, 80),
        Setpoint("tank_upper_autumn", "data_t_zas", "txt512", 106, 107, 10, 80),
        Setpoint("tank_upper_winter", "data_t_zas", "txt513", 108, 109, 10, 80),
        Setpoint("tank_lower_spring", "data_t_zas", "txt514", 110, 111, 10, 85),
        Setpoint("tank_lower_summer", "data_t_zas", "txt515", 112, 113, 10, 85),
        Setpoint("tank_lower_autumn", "data_t_zas", "txt516", 114, 115, 10, 85),
        Setpoint("tank_lower_winter", "data_t_zas", "txt517", 116, 117, 10, 85),
        Setpoint("circuit_1_curve", "data_t_ek1", "txt574", 141, 142, 1, 60),
        Setpoint("circuit_1_setback", "data_t_ek1", "txt570", 125, 126, 1, 50),
        Setpoint("circuit_1_shift", "data_t_ek1", "txt575", 143, 144, -9, 9),
        Setpoint("circuit_1_min", "data_t_ek1", "txt572", 137, 138, 10, 79),
        Setpoint("circuit_1_max", "data_t_ek1", "txt573", 139, 140, 11, 80),
        Setpoint("circuit_2_curve", "data_t_ek2", "txt584", 171, 172, 1, 60),
        Setpoint("circuit_2_setback", "data_t_ek2", "txt580", 155, 156, 1, 50),
        Setpoint("circuit_2_shift", "data_t_ek2", "txt585", 173, 174, -9, 9),
        Setpoint("circuit_2_min", "data_t_ek2", "txt582", 167, 168, 10, 79),
        Setpoint("circuit_2_max", "data_t_ek2", "txt583", 169, 170, 11, 80),
        Setpoint("fireplace_start", "data_t_krb", "txt596", 441, 442, 50, 80),
        Setpoint("fireplace_hysteresis", "data_t_krb", "txt597", 443, 444, 5, 20),
        Setpoint("solar_difference", "data_t_sol", "txt595", 425, 426, 5, 30),
        Setpoint("pool_on", "data_t_baz", "txt195", 480, 481, 10, 37),
        Setpoint("pool_off", "data_t_baz", "txt196", 452, 453, 11, 38),
        Setpoint("cooling_on", "data_t_chl", "txt194", 180, 181, 6, 40),
        Setpoint("cooling_off", "data_t_chl", "txt193", 182, 183, 5, 39),
    )
}


def parse_temperature(value: str) -> float | None:
    """Parse a temperature, returning None for a disconnected sensor."""
    value = value.strip()
    if value in EMPTY_TEMPERATURES:
        return None
    return float(value)


def parse_counter_hours(value: str) -> float:
    """Parse an operating hours counter such as 'SP1: 007500:50'."""
    hours, minutes = map(int, value.split()[-1].split(":"))
    return round(hours + minutes / 60, 2)


def parse_percent(value: str) -> int:
    """Parse a percentage such as '015%'."""
    return int(value.strip().rstrip("%"))


def get_output_mode(data: dict[str, str], output: DigitalOutput) -> OutputMode | None:
    """Return the active mode of an output, or None when the controller reports none."""
    for key, mode in output.mode_keys.items():
        if data.get(key) == "1":
            return mode
    return None


def normalize_host(host: str) -> str:
    """Return a base URL for the given host or URL."""
    host = host.strip().rstrip("/")
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host


class IQR23Client:
    """Client of the controller's XML/CGI web interface."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, master_password: str
    ) -> None:
        self._session = session
        self.host = normalize_host(host)
        self._master_password = master_password
        # The controller keeps a single global login, so writes and reads must not interleave.
        self._lock = asyncio.Lock()

    async def _get_xml(self, file: str) -> dict[str, str]:
        url = f"{self.host}/{file}.xml"
        try:
            async with self._session.get(url, timeout=REQUEST_TIMEOUT) as response:
                response.raise_for_status()
                text = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise IQR23ConnectionError(f"Error fetching {url}: {err}") from err
        try:
            return xmltodict.parse(text)["response"] or {}
        except (KeyError, TypeError, ValueError) as err:
            raise IQR23ConnectionError(f"Invalid XML from {url}: {err}") from err

    async def async_get_firmware_version(self) -> str:
        """Return the firmware version string; used to validate the connection."""
        data = await self._get_xml("data")
        try:
            return data["_accvers"]
        except KeyError as err:
            raise IQR23ConnectionError("Response does not look like iQ R23") from err

    async def async_fetch(self) -> tuple[dict[str, str], list[str]]:
        """Fetch all data files.

        Returns the merged data and the names of files that failed. Raises only
        when every file failed.
        """
        async with self._lock:
            results = await asyncio.gather(
                *(self._get_xml(file) for file in DATA_FILES), return_exceptions=True
            )
        data: dict[str, str] = {}
        failed: list[str] = []
        for file, result in zip(DATA_FILES, results, strict=True):
            if isinstance(result, BaseException):
                _LOGGER.debug("Failed to load %s.xml from %s: %s", file, self.host, result)
                failed.append(file)
                continue
            data.update(result)
        if not data:
            raise IQR23ConnectionError(f"Unable to load any data from {self.host}")
        return data, failed

    async def _login(self, password: str) -> None:
        try:
            async with self._session.post(
                f"{self.host}/login.html", data={"pass": password}, timeout=REQUEST_TIMEOUT
            ) as response:
                if response.status != 200:
                    raise IQR23AuthError(f"Login returned HTTP {response.status}")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise IQR23ConnectionError(f"Login failed: {err}") from err

    async def _press_button(self, button: int) -> None:
        try:
            async with self._session.get(
                f"{self.host}/t_but.cgi", params={"but": button}, timeout=REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise IQR23ConnectionError(f"Button {button} press failed: {err}") from err

    @asynccontextmanager
    async def _service_mode(self) -> AsyncIterator[None]:
        """Log in with the master password; buttons are ignored without it."""
        await self._login(self._master_password)
        try:
            yield
        finally:
            # Always log out, otherwise the controller stays in service mode.
            try:
                await self._login("")
            except IQR23Error as err:
                _LOGGER.warning("Logout from %s failed: %s", self.host, err)

    async def async_set_output_mode(self, output_key: str, mode: OutputMode) -> None:
        """Switch a digital output to the given mode and persist the setting."""
        button = DIGITAL_OUTPUTS[output_key].mode_buttons[OutputMode(mode)]
        async with self._lock, self._service_mode():
            await self._press_button(button)
            await self._press_button(SAVE_BUTTON)

    async def _get_setpoint(self, setpoint: Setpoint) -> int:
        data = await self._get_xml(setpoint.file)
        try:
            return int(data[setpoint.value_key])
        except (KeyError, TypeError, ValueError) as err:
            raise IQR23ConnectionError(f"Missing value of {setpoint.key}") from err

    async def async_set_setpoint(self, key: str, value: int) -> None:
        """Press -/+ until the setpoint reaches the value, then persist it.

        The controller only offers relative buttons, so the result is read back;
        a second round makes up for presses the controller dropped.
        """
        setpoint = SETPOINTS[key]
        if not setpoint.min_value <= value <= setpoint.max_value:
            raise ValueError(f"{value} is out of range of {key}")
        async with self._lock, self._service_mode():
            for _ in range(2):
                current = await self._get_setpoint(setpoint)
                presses = (value - current) // setpoint.step
                if not presses:
                    break
                button = setpoint.plus_button if presses > 0 else setpoint.minus_button
                for _ in range(abs(presses)):
                    await self._press_button(button)
            current = await self._get_setpoint(setpoint)
            # Persist whatever was reached, so the controller does not revert on restart.
            await self._press_button(SAVE_BUTTON)
        if current != value:
            raise IQR23Error(f"{key} stopped at {current} instead of {value}")
