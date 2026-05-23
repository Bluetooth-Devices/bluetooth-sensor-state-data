"""Tests for the public BluetoothData API.

``changed_manufacturer_data`` is covered by ``test_init``; this module
exercises the rest of the public surface that subclasses rely on:
``supported``, ``update`` and ``update_signal_strength``.
"""

from __future__ import annotations

from habluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass, Units
from sensor_state_data.device import DeviceKey

from bluetooth_sensor_state_data import SIGNAL_STRENGTH_KEY, BluetoothData


def make_service_info(rssi: int = -63) -> BluetoothServiceInfo:
    return BluetoothServiceInfo(
        name="Test Sensor",
        address="AA:BB:CC:DD:EE:FF",
        rssi=rssi,
        service_data={},
        source="local",
        manufacturer_data={1: b"\x00\x01"},
        service_uuids=["0000fff0-0000-1000-8000-00805f9b34fb"],
    )


class _StubData(BluetoothData):
    """Concrete BluetoothData that registers a configurable set of devices."""

    def __init__(
        self,
        *,
        device_ids: tuple[str | None, ...] = ("sensor",),
        fire_once: bool = False,
    ) -> None:
        super().__init__()
        self._device_ids = device_ids
        self._fire_once = fire_once
        self._update_count = 0

    def _start_update(self, data: BluetoothServiceInfo) -> None:
        self._update_count += 1
        for device_id in self._device_ids:
            self.set_device_type("Test Device", device_id)
        # A transient event fired only on the first update, used to verify
        # that update() clears stale events between calls.
        if self._fire_once and self._update_count == 1:
            self.fire_event("button", "press", device_id=self._device_ids[0])


def test_supported_true_when_device_registered() -> None:
    assert _StubData().supported(make_service_info()) is True


def test_supported_false_when_no_device_registered() -> None:
    assert _StubData(device_ids=()).supported(make_service_info()) is False


def test_update_emits_signal_strength_sensor() -> None:
    data = _StubData()
    update = data.update(make_service_info(rssi=-42))

    key = DeviceKey(SIGNAL_STRENGTH_KEY, "sensor")
    assert update.entity_values[key].native_value == -42

    description = update.entity_descriptions[key]
    assert description.device_class == DeviceClass.SIGNAL_STRENGTH
    assert (
        description.native_unit_of_measurement
        == Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )


def test_update_signal_strength_for_every_registered_device() -> None:
    data = _StubData(device_ids=("a", "b", "c"))
    update = data.update(make_service_info(rssi=-55))

    for device_id in ("a", "b", "c"):
        key = DeviceKey(SIGNAL_STRENGTH_KEY, device_id)
        assert update.entity_values[key].native_value == -55


def test_update_clears_transient_events_between_calls() -> None:
    data = _StubData(fire_once=True)

    first = data.update(make_service_info())
    assert first.events, "first update should carry the fired event"

    second = data.update(make_service_info())
    assert second.events == {}, "transient events must not leak into later updates"
