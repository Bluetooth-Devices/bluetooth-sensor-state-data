from __future__ import annotations

__version__ = "1.1.0"

from abc import abstractmethod

from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import SensorUpdate
from sensor_state_data.data import DeviceClass, SensorData
from sensor_state_data.units import SIGNAL_STRENGTH_DECIBELS_MILLIWATT


class BluetoothData(SensorData):
    """Update bluetooth data."""

    @abstractmethod
    def update(self, data: BluetoothServiceInfo) -> None:
        """Update the data."""

    def supported(self, data: BluetoothServiceInfo) -> bool:
        """Return True if the device is supported."""
        self.generate_update(data)
        return bool(self._device_id_to_type)

    def generate_update(self, data: BluetoothServiceInfo) -> SensorUpdate:
        """Update a bluetooth device."""
        self.update_rssi(data.rssi)
        return super().generate_update(data)

    def update_rssi(self, native_value: int | float) -> None:
        """Quick update for an rssi sensor."""
        self.update_sensor(
            key="rssi",
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            native_value=native_value,
            device_class=DeviceClass.SIGNAL_STRENGTH,
        )
