import logging
from homeassistant.components.light import (
    LightEntity,
    SUPPORT_COLOR,
    SUPPORT_BRIGHTNESS,
)
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_HS_COLOR, LightEntity, SUPPORT_COLOR, SUPPORT_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.util.color import color_hs_to_RGB
from Crypto.Cipher import AES
from bleak import BleakClient
import asyncio

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sunset_lamp"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up the Sunset Lamp light entity."""
    name = config_entry.data.get("name", "Sunset Lamp")
    mac_address = config_entry.data.get("mac_address")
    
    lamp_controller = SunsetLampController(mac_address)
    hass.data[DOMAIN][config_entry.entry_id] = lamp_controller
    
    await lamp_controller.connect()

    async_add_entities([SunsetLamp(lamp_controller, name)])


class PayloadGenerator:
    """Generates encrypted payloads for commands."""
    
    KEY = bytes([
        0x34, 0x52, 0x2A, 0x5B, 0x7A, 0x6E, 0x49, 0x2C,
        0x08, 0x09, 0x0A, 0x9D, 0x8D, 0x2A, 0x23, 0xF8
    ])
    HEADER = bytes([0x54, 0x52, 0x0, 0x57])
    GROUP_ID = 1

    def __init__(self):
        self.crypt = AES.new(self.KEY, AES.MODE_ECB)

    def get_rgb_payload(self, red, green, blue, brightness=100, speed=100):
        """Generate encrypted payload for RGB settings."""
        payload = bytearray(16)
        payload[:4] = self.HEADER
        payload[4] = 2  # CommandType.Rgb
        payload[5] = self.GROUP_ID
        payload[7:10] = red, green, blue
        payload[10] = brightness
        payload[11] = speed
        result = self.crypt.encrypt(bytes(payload))
        _LOGGER.info(result)
        return ''.join(f'{x:02x}' for x in result)


class SunsetLampController:
    """Handles connection and communication with the lamp."""

    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.client = None

    async def connect(self):
        """Establish connection with the lamp."""
        if self.client and self.client.is_connected:
            _LOGGER.info("Already connected.")
            return
        try:
            self.client = BleakClient(self.mac_address)
            await self.client.connect()
            if self.client.is_connected:
                _LOGGER.info(f"Connected to device: {self.mac_address}")
        except Exception as e:
            _LOGGER.error(f"Connection error: {e}")
            self.client = None

    async def disconnect(self):
        """Disconnect from the lamp."""
        if self.client:
            await self.client.disconnect()
            _LOGGER.info(f"Disconnected from device: {self.mac_address}")
            self.client = None

    async def send_command(self, command: bytes):
        _LOGGER.info("COMMAND IS ")
        _LOGGER.info(command)
        """Send a command to the lamp."""
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Reconnecting...")
            await self.connect()
        try:
            await self.client.write_gatt_char("0000ac52-1212-efde-1523-785fedbeda25", bytes.fromhex(command))  # Adjust the handle as necessary
            _LOGGER.info(f"Command sent: {command.hex()}")
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")


class SunsetLamp(LightEntity):
    """Representation of the Sunset Lamp as a light entity."""

    def __init__(self, lamp_controller, name):
        """Initialize the lamp."""
        self._name = name
        self._lamp_controller = lamp_controller
        self._is_on = False
        self._brightness = 255
        self._hs_color = (0, 0)
        self._payload_generator = PayloadGenerator()

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this lamp."""
        return f"sunset_lamp_{self._name.lower().replace(' ', '_')}"

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    @property
    def supported_features(self):
        """Return the supported features of the light."""
        return SUPPORT_COLOR | SUPPORT_BRIGHTNESS

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the color of the light in HS format."""
        return self._hs_color

    async def async_turn_on(self, **kwargs):
        """Turn on the lamp."""
        self._is_on = True

        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_HS_COLOR in kwargs:
            self._hs_color = kwargs[ATTR_HS_COLOR]

        r, g, b = color_hs_to_RGB(*self._hs_color)
        brightness = int(self._brightness / 255 * 100)

        command = self._payload_generator.get_rgb_payload(r, g, b, brightness)
        await self._lamp_controller.send_command(command)

    async def async_turn_off(self, **kwargs):
        """Turn off the lamp."""
        self._is_on = False

        # Sending a "turn off" command (adjust the payload if necessary)
        command = self._payload_generator.get_rgb_payload(0, 0, 0, 0)
        await self._lamp_controller.send_command(command)

    async def async_update(self):
        """Fetch new state data for the light."""
        # Implement if the lamp supports state polling.
        pass
