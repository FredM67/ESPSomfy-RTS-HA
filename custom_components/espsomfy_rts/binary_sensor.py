"""Binary sensors related to ESPSomfy-RTS-HA."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EVT_GROUPSTATE, EVT_SHADESTATE
from .controller import ESPSomfyController
from .entity import ESPSomfyShadeEntity


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
        for shade in controller.api.shades:
            try:
                if "sunSensor" in shade:
                    if shade["sunSensor"] is True:
                        new_entities.append(ESPSomfyFlagSensor(controller, shade, "sun"))
                        new_entities.append(ESPSomfyFlagSensor(controller, shade, "wind"))
                    elif "shadeType" in shade:
                        match shade["shadeType"]:
                            case 3:
                                new_entities.append(ESPSomfyFlagSensor(controller, shade, "wind"))
                elif "shadeType" in shade:
                    match shade["shadeType"]:
                        case 3:
                            new_entities.append(ESPSomfyFlagSensor(controller, shade, "sun"))
                            new_entities.append(ESPSomfyFlagSensor(controller, shade, "wind"))
            except KeyError:
                pass
        for group in controller.api.groups:
            try:
                if "sunSensor" in group and group["sunSensor"] is True:
                    new_entities.append(ESPSomfyFlagSensor(controller, group, "sun"))
                    new_entities.append(ESPSomfyFlagSensor(controller, group, "wind"))
            except KeyError:
                pass
    if new_entities:
        async_add_entities(new_entities)


# Flag bitmasks and config per sensor kind
_FLAG_CONFIG = {
    "sun": {
        "mask": 0x20,
        "uid_prefix": "sun",
        "uid_group_prefix": "sun_group",
        "icon_on": "mdi:weather-sunny",
        "icon_off": "mdi:weather-sunny-off",
        "name_suffix": "Sun",
    },
    "wind": {
        "mask": 0x10,
        "uid_prefix": "wind",
        "uid_group_prefix": "wind_group",
        "icon_on": "mdi:wind-power",
        "icon_off": "mdi:wind-power-outline",
        "name_suffix": "Wind",
    },
}


class ESPSomfyFlagSensor(ESPSomfyShadeEntity, BinarySensorEntity):
    """A binary sensor for sun or wind flag state."""

    def __init__(
        self, controller: ESPSomfyController, data: dict, kind: str
    ) -> None:
        """Initialize a new flag sensor (kind: 'sun' or 'wind')."""
        super().__init__(controller=controller, data=data)
        cfg = _FLAG_CONFIG[kind]
        self._flag_mask: int = cfg["mask"]
        self._icon_on: str = cfg["icon_on"]
        self._icon_off: str = cfg["icon_off"]
        self._attr_name = data["name"]
        self._attr_has_entity_name = False

        if self._entity_type == "group":
            self._attr_unique_id = (
                f"{cfg['uid_group_prefix']}_{controller.unique_id}_{self._group_id}"
            )
        else:
            self._attr_unique_id = (
                f"{cfg['uid_prefix']}_{controller.unique_id}_{self._shade_id}"
            )

        self._attr_is_on = bool((int(data.get("flags", 0)) & self._flag_mask) == self._flag_mask)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        data = self.coordinator.data
        if (
            self._entity_type == "motor"
            and data.get("shadeId") == self._shade_id
            and data.get("event") == EVT_SHADESTATE
            and "flags" in data
        ) or (
            self._entity_type == "group"
            and data.get("groupId") == self._group_id
            and data.get("event") == EVT_GROUPSTATE
            and "flags" in data
        ):
            new_state = bool((int(data["flags"]) & self._flag_mask) == self._flag_mask)
            if self._attr_is_on != new_state:
                self._attr_is_on = new_state
                self.async_write_ha_state()

    @property
    def icon(self) -> str:
        """Icon depending on sensor state."""
        return self._icon_on if self.is_on else self._icon_off


# Keep old class names as aliases for backwards compatibility
ESPSomfySunSensor = lambda controller, data: ESPSomfyFlagSensor(controller, data, "sun")  # noqa: E731
ESPSomfyWindSensor = lambda controller, data: ESPSomfyFlagSensor(controller, data, "wind")  # noqa: E731
