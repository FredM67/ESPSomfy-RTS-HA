"""Sensors related to ESPSomfy-RTS-HA."""

from __future__ import annotations

from dataclasses import dataclass
import statistics
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfDataRate,
    UnitOfInformation,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, EVT_ETHERNET, EVT_MEMSTATUS, EVT_WIFISTRENGTH
from .controller import ESPSomfyController
from .entity import ESPSomfyEntity


@dataclass
class ESPSomfyDiagSensorDescription(SensorEntityDescription):
    """A base class descriptor for a sensor entity."""

    id: str | None = None
    events: dict | None = None
    native_value: Any | None = None
    min_interval: int = 0
    value_count: int = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up shades for the shade controller."""

    controller = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    data = controller.api.get_config()
    if "serverId" in data:
        if "hostname" in data:
            new_entities.append(
                ESPSomfyDiagSensor(
                    controller=controller,
                    cfg=ESPSomfyDiagSensorDescription(
                        key="host_name",
                        entity_category=EntityCategory.DIAGNOSTIC,
                        name="Hostname",
                        native_value=data["hostname"],
                        events={},
                        icon="mdi:tag-text",
                    ),
                    data=data,
                )
            )
        if "chipModel" in data:
            chip_model = "ESP32"
            if len(data["chipModel"]):
                chip_model += "-"
                chip_model += data["chipModel"]
            new_entities.append(
                ESPSomfyDiagSensor(
                    controller=controller,
                    cfg=ESPSomfyDiagSensorDescription(
                        key="chip_model",
                        entity_category=EntityCategory.DIAGNOSTIC,
                        name="Chip Type",
                        native_value=chip_model.upper(),
                        events={},
                        icon="mdi:cpu-32-bit",
                    ),
                    data=data,
                )
            )
        if "connType" in data:
            new_entities.append(
                ESPSomfyDiagSensor(
                    controller=controller,
                    cfg=ESPSomfyDiagSensorDescription(
                        key="conn_type",
                        entity_category=EntityCategory.DIAGNOSTIC,
                        name="Connection",
                        events={},
                        native_value=data["connType"],
                        icon="mdi:connection",
                    ),
                    data=data,
                )
            )
            if data["connType"] == "Wifi":
                new_entities.append(ESPSomfyWifiStrengthSensor(controller, data))
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="wifi_ssid",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            name="Wifi SSID",
                            icon="mdi:wifi-cog",
                            native_value=data.get("ssid", ""),
                            events={EVT_WIFISTRENGTH: "ssid"},
                        ),
                        data=data,
                    )
                )
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="wifi_channel",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            name="Wifi Channel",
                            icon="mdi:radio-tower",
                            events={EVT_WIFISTRENGTH: "channel"},
                        ),
                        data=data,
                    )
                )
            elif data["connType"] == "Ethernet":
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="eth_speed",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            state_class=SensorStateClass.MEASUREMENT,
                            device_class=SensorDeviceClass.DATA_RATE,
                            unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
                            name="Connection Speed",
                            icon="mdi:lan-connect",
                            native_value=data.get("speed", 100),
                            events={EVT_ETHERNET: "speed"},
                        ),
                        data=data,
                    )
                )
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="eth_full_duplex",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            name="Full Duplex",
                            icon="mdi:sync",
                            native_value=bool(data.get("fullduplex", True)),
                            events={EVT_ETHERNET: "fullduplex"},
                        ),
                        data=data,
                    )
                )
        if "memory" in data:
            mem = data["memory"]
            if "free" in mem:
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="free_memory",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            device_class=SensorDeviceClass.DATA_SIZE,
                            name="Free Memory",
                            icon="mdi:memory",
                            state_class=SensorStateClass.MEASUREMENT,
                            unit_of_measurement=UnitOfInformation.BYTES,
                            suggested_display_precision=0,
                            native_value=mem["free"],
                            min_interval=25,
                            value_count=15,
                            events={EVT_MEMSTATUS: "free"},
                        ),
                        data=data,
                    )
                )
            if "max" in mem:
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="max_memory",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            name="Max Memory",
                            icon="mdi:memory",
                            unit_of_measurement=UnitOfInformation.BYTES,
                            state_class=SensorStateClass.MEASUREMENT,
                            suggested_display_precision=0,
                            native_value=mem["max"],
                            min_interval=30,
                            value_count=15,
                            events={EVT_MEMSTATUS: "max"},
                        ),
                        data=data,
                    )
                )
            if "min" in mem:
                new_entities.append(
                    ESPSomfyDiagSensor(
                        controller=controller,
                        cfg=ESPSomfyDiagSensorDescription(
                            key="min_memory",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            name="Min Memory",
                            icon="mdi:memory",
                            min_interval=30,
                            value_count=15,
                            unit_of_measurement=UnitOfInformation.BYTES,
                            state_class=SensorStateClass.MEASUREMENT,
                            suggested_display_precision=0,
                            native_value=mem["min"],
                            events={EVT_MEMSTATUS: "min"},
                        ),
                        data=data,
                    )
                )

        new_entities.append(
            ESPSomfyDiagSensor(
                controller=controller,
                cfg=ESPSomfyDiagSensorDescription(
                    key="ip_addresss",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    name="IP Address",
                    icon="mdi:ip",
                    events={},
                    native_value=controller.api.get_data()["host"],
                ),
                data=data,
            )
        )
    if new_entities:
        async_add_entities(new_entities)


class ESPSomfyDiagSensor(ESPSomfyEntity, SensorEntity):
    """A diagnostic entity for the hub."""

    def __init__(
        self, controller: ESPSomfyController, cfg: ESPSomfyDiagSensorDescription, data
    ) -> None:
        """Initialize a new diagnostic sensor."""
        super().__init__(controller=controller, data=data)
        self.events = {}
        self._attr_entity_category = cfg.entity_category
        self._attr_unique_id = f"{cfg.key}_{controller.unique_id}"
        self._attr_name = cfg.name
        self._attr_device_class = cfg.device_class
        self._attr_native_unit_of_measurement = cfg.unit_of_measurement
        self._attr_state_class = cfg.state_class
        self.events = cfg.events
        self._attr_icon = cfg.icon
        self._attr_native_value = cfg.native_value
        self._last_recorded = dt_util.utcnow()
        self._min_interval = cfg.min_interval
        self._value_count = cfg.value_count
        self._values = []
        self._attr_suggested_display_precision = cfg.suggested_display_precision

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        data = self.coordinator.data
        if (
            "event" in data
            and data["event"] in self.events
        ):
            evt = self.events[data["event"]]
            if evt in data:
                self._values.append(data[evt])
                val = data[evt]
                if (
                    dt_util.utcnow() > self._last_recorded + timedelta(seconds=self._min_interval)
                    or len(self._values) >= self._value_count
                    or not self._available
                ):
                    self._available = True
                    if self._value_count > 1:
                        val = int(statistics.median(self._values))
                    self._values.clear()
                    self._last_recorded = dt_util.utcnow()
                    if val != self._attr_native_value:
                        self._attr_native_value = val
                        self.async_write_ha_state()
                elif self._attr_native_value is None:
                    self._attr_native_value = val
                    self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """Indicates that the sensor should not poll."""
        return False


class ESPSomfyWifiStrengthSensor(ESPSomfyDiagSensor):
    """A wifi strength sensor indicating the current connection strength."""

    def __init__(self, controller: ESPSomfyController, data) -> None:
        """Initialize a new Wifi strength Sensor."""
        super().__init__(
            controller=controller,
            cfg=ESPSomfyDiagSensorDescription(
                key="wifi_sensor",
                device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                entity_category=EntityCategory.DIAGNOSTIC,
                unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                state_class=SensorStateClass.MEASUREMENT,
                name="Wifi Strength",
                icon="mdi:wifi",
                min_interval=30,
                value_count=15,
                events={EVT_WIFISTRENGTH: "strength"},
            ),
            data=data,
        )

    @property
    def should_poll(self) -> bool:
        """Indicates that the sensor should not poll."""
        return False
