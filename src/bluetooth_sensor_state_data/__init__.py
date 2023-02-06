from __future__ import annotations

__version__ = "1.6.1"

from abc import abstractmethod

from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass, SensorData, SensorUpdate, Units

SIGNAL_STRENGTH_KEY = DeviceClass.SIGNAL_STRENGTH.value

__all__ = ["BluetoothData", "SIGNAL_STRENGTH_KEY"]


class BluetoothData(SensorData):
    """Update bluetooth data."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__()
        self._last_manufacturer_data_set_by_source: dict[
            str, set[tuple[int, bytes]]
        ] = {}

    def changed_manufacturer_data(
        self, data: BluetoothServiceInfo, exclude_ids: set[int] | None = None
    ) -> dict[int, bytes]:
        """Find changed manufacturer data.

        This function is not re-entrant. It must only
        be called once per update.
        """
        manufacturer_data = data.manufacturer_data
        source = data.source

        last_manufacturer_data_set = (
            self._last_manufacturer_data_set_by_source.setdefault(source, set())
        )
        if exclude_ids:
            # If there are specific manufacturer data IDs to exclude,
            # then remove them from the set of manufacturer data.
            manufacturer_data_set = {
                key_val
                for key_val in manufacturer_data.items()
                if key_val[0] not in exclude_ids
            }
        else:
            manufacturer_data_set = set(manufacturer_data.items())
        self._last_manufacturer_data_set_by_source[source] = manufacturer_data_set

        if not last_manufacturer_data_set:
            # If there is no previous data and there is only one value
            # return it
            return (
                dict(manufacturer_data_set) if len(manufacturer_data_set) == 1 else {}
            )

        return dict(manufacturer_data_set - last_manufacturer_data_set)

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
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                native_value=native_value,
                device_class=DeviceClass.SIGNAL_STRENGTH,
                device_id=device_id,
            )
