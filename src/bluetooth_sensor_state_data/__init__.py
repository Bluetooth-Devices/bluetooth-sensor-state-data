from __future__ import annotations

__version__ = "1.9.0"

from abc import abstractmethod

from bluetooth_data_tools import parse_advertisement_data_bytes
from habluetooth import BluetoothServiceInfo, BluetoothServiceInfoBleak
from sensor_state_data import DeviceClass, SensorData, SensorUpdate, Units

SIGNAL_STRENGTH_KEY = DeviceClass.SIGNAL_STRENGTH.value

__all__ = ["BluetoothData", "SIGNAL_STRENGTH_KEY"]


class BluetoothData(SensorData):
    """Update bluetooth data."""

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__()
        self._last_manufacturer_data_by_source: dict[str, dict[int, bytes]] = {}

    def changed_manufacturer_data(
        self,
        data: BluetoothServiceInfo | BluetoothServiceInfoBleak,
        exclude_ids: set[int] | None = None,
    ) -> dict[int, bytes]:
        """Find changed manufacturer data.

        This function is not re-entrant. It must only
        be called once per update.
        """
        if hasattr(data, "raw") and data.raw:
            # If we have the raw data we don't need to work out
            # which one is the newest.
            _, _, _, changed_manufacturer_data, _ = parse_advertisement_data_bytes(
                data.raw
            )
            if exclude_ids:
                # If there are specific manufacturer data IDs to exclude,
                # then remove them from the set of manufacturer data.
                changed_manufacturer_data = {
                    k: v
                    for k, v in changed_manufacturer_data.items()
                    if k not in exclude_ids
                }
            # If we can't work out the changed manufacturer data
            # fall back to the normal method.
            if changed_manufacturer_data:
                return changed_manufacturer_data

        manufacturer_data = data.manufacturer_data
        source = data.source
        last_manufacturer_data = self._last_manufacturer_data_by_source.get(source)

        if exclude_ids:
            # If there are specific manufacturer data IDs to exclude,
            # then remove them from the set of manufacturer data.
            new_manufacturer_data = {
                k: v for k, v in manufacturer_data.items() if k not in exclude_ids
            }
        else:
            new_manufacturer_data = manufacturer_data

        self._last_manufacturer_data_by_source[source] = manufacturer_data
        single_manufacturer_data = len(new_manufacturer_data) == 1

        if not last_manufacturer_data or single_manufacturer_data:
            # If there is no previous data and there is only one value
            # return it
            return new_manufacturer_data if single_manufacturer_data else {}

        return dict(new_manufacturer_data.items() - last_manufacturer_data.items())

    @abstractmethod
    def _start_update(
        self, data: BluetoothServiceInfo | BluetoothServiceInfoBleak
    ) -> None:
        """Update the data."""

    def supported(self, data: BluetoothServiceInfo | BluetoothServiceInfoBleak) -> bool:
        """Return True if the device is supported."""
        self._start_update(data)
        return bool(self._device_id_to_type)

    def update(
        self, data: BluetoothServiceInfo | BluetoothServiceInfoBleak
    ) -> SensorUpdate:
        """Update a device."""
        # Ensure events from previous
        # updates are not carried over
        # as events are transient.
        self._events_updates.clear()
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
