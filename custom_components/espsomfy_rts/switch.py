"""Switches related to ESPSomfy-RTS-HA."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
                if "shadeType" in shade and (
                    int(shade["shadeType"]) == 9 or int(shade["shadeType"]) == 10
                ):
                    new_entities.append(
                        ESPSomfyBinarySwitch(controller=controller, data=shade)
                    )
                elif "sunSensor" in shade:
                    if shade["sunSensor"] is True:
                        new_entities.append(
                            ESPSomfySunSwitch(controller=controller, data=shade)
                        )
                elif "shadeType" in shade:
                    match shade["shadeType"]:
                        case 3:
                            new_entities.append(
                                ESPSomfySunSwitch(controller=controller, data=shade)
                            )
            except KeyError:
                pass

        for group in controller.api.groups:
            try:
                if "sunSensor" in group and group["sunSensor"] is True:
                    new_entities.append(
                        ESPSomfySunSwitch(controller=controller, data=group)
                    )
            except KeyError:
                pass
    if new_entities:
        async_add_entities(new_entities)


class ESPSomfySunSwitch(ESPSomfyShadeEntity, SwitchEntity):
    """A sun flag switch for toggling sun mode."""

    def __init__(self, controller: ESPSomfyController, data) -> None:
        """Initialize a new SunSwitch."""
        super().__init__(controller=controller, data=data)
        self._attr_icon = "mdi:white-balance-sunny"
        self._attr_name = data["name"]
        self._attr_has_entity_name = False

        if self._entity_type == "group":
            self._attr_unique_id = (
                f"sunswitch_group_{controller.unique_id}_{self._group_id}"
            )
        else:
            self._attr_unique_id = f"sunswitch_{controller.unique_id}_{self._shade_id}"

        self._attr_is_on = bool((int(data.get("flags", 0)) & 0x01) == 0x01)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        data = self.coordinator.data
        if (
            self._entity_type == "motor"
            and data.get("shadeId") == self._shade_id
            and data.get("event") == EVT_SHADESTATE
            and "flags" in data
        ):
            self._attr_is_on = bool((int(data["flags"]) & 0x01) == 0x01)
            self.async_write_ha_state()
        elif (
            self._entity_type == "group"
            and data.get("groupId") == self._group_id
            and data.get("event") == EVT_GROUPSTATE
            and "flags" in data
        ):
            self._attr_is_on = bool((int(data["flags"]) & 0x01) == 0x01)
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if self._entity_type == "motor":
            await self.coordinator.api.sun_flag_on(self._shade_id)
        else:
            await self.coordinator.api.sun_flag_group_on(self._group_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if self._entity_type == "motor":
            await self.coordinator.api.sun_flag_off(self._shade_id)
        else:
            await self.coordinator.api.sun_flag_group_off(self._group_id)


class ESPSomfyBinarySwitch(ESPSomfyShadeEntity, SwitchEntity):
    """A binary switch for toggling a dry contact."""

    def __init__(self, controller: ESPSomfyController, data) -> None:
        """Initialize a new BinarySwitch."""
        super().__init__(controller=controller, data=data)
        self._attr_name = data["name"]
        self._attr_has_entity_name = False
        self._binaryswitch_type = data["shadeType"]
        self._attr_unique_id = f"binaryswitch_{controller.unique_id}_{self._shade_id}"
        self._flip_commands = bool(data.get("flipCommands", False))
        self._attr_is_on = bool((int(data.get("position", 0))) > 0)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        data = self.coordinator.data
        if (
            "position" in data
            and data.get("shadeId") == self._shade_id
        ):
            self._attr_is_on = bool((int(data["position"])) > 0)
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if self._binaryswitch_type == 10:
            if self._flip_commands:
                await self.coordinator.api.close_shade(self._shade_id)
            else:
                await self.coordinator.api.open_shade(self._shade_id)
        else:
            await self.coordinator.api.toggle_shade(self._shade_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if self._binaryswitch_type == 10:
            if self._flip_commands:
                await self.coordinator.api.open_shade(self._shade_id)
            else:
                await self.coordinator.api.close_shade(self._shade_id)
        else:
            await self.coordinator.api.toggle_shade(self._shade_id)
