from __future__ import annotations

__version__ = "1.4.6"

from abc import abstractmethod

from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass, SensorData, SensorUpdate
from sensor_state_data.units import SIGNAL_STRENGTH_DECIBELS_MILLIWATT

SIGNAL_STRENGTH_KEY = DeviceClass.SIGNAL_STRENGTH.value

__all__ = ["BluetoothData", "SIGNAL_STRENGTH_KEY"]


class BluetoothData(SensorData):
    """Update bluetooth data."""

    @abstractmethod
    def _start_update(self, data: BluetoothServiceInfo) -> None:
        """Update the data."""

    def supported(self, data: BluetoothServiceInfo) -> bool:
        """Return True if the device is supported."""
        self._start_update(data)
        return bool(self._device_id_to_type)

    def update(self, data: BluetoothServiceInfo) -> SensorUpdate:
        """Update a device."""
        self._start_update(data)
        self.update_signal_strength(data.rssi)
        return self._finish_update()

    def update_signal_strength(self, native_value: int | float) -> None:
        """Quick update for an signal strength sensor."""
        for device_id in self._device_id_to_type:
            self.update_sensor(
                key=DeviceClass.SIGNAL_STRENGTH.value,
                native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                native_value=native_value,
                device_class=DeviceClass.SIGNAL_STRENGTH,
                device_id=device_id,
            )
