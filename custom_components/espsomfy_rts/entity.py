"""ESPSomfy parent entity class."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVT_CONNECTED, MANUFACTURER
from .controller import ESPSomfyController


class ESPSomfyEntity(CoordinatorEntity[ESPSomfyController], Entity):
    """Base entity for the ESPSomfy controller."""

    def __init__(self, *, data: Any, controller: ESPSomfyController) -> None:
        """Initialize the entity."""
        super().__init__(coordinator=controller)
        self.controller = controller
        self._available = True

    @property
    def should_poll(self) -> bool:
        """Indicates that the entity should not poll."""
        return False

    @property
    def available(self) -> bool:
        """Indicates whether the entity is available."""
        return self._available

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Subclasses must call super()._handle_coordinator_update() first and
        return early if it returns True (meaning the EVT_CONNECTED event was
        handled and async_write_ha_state already called).
        """
        if self.registry_entry and self.registry_entry.disabled:
            return
        data = self.coordinator.data
        if (
            data.get("event", "") == EVT_CONNECTED
            and "connected" in data
        ):
            self._available = bool(data["connected"])
            self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo | None:
        """Device info."""
        return DeviceInfo(
            configuration_url=self.controller.api.get_config_url(),
            identifiers={(DOMAIN, self.controller.unique_id)},
            name=self.controller.device_name,
            manufacturer=MANUFACTURER,
            model=self.controller.model,
            sw_version=self.controller.version,
            hw_version=None,
        )


class ESPSomfyShadeEntity(ESPSomfyEntity):
    """Base entity for ESPSomfy shades and groups."""

    def __init__(self, *, data: Any, controller: ESPSomfyController) -> None:
        """Initialize the entity."""
        super().__init__(data=data, controller=controller)
        self._data = data
        self._shade_id: int | None = data.get("shadeId")
        self._group_id: int | None = data.get("groupId")
        self._entity_type = "group" if "groupId" in data else "motor"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Device info."""
        unique_suffix = (
            f"shade_{self._shade_id}"
            if self._entity_type == "motor"
            else f"group_{self._group_id}"
        )
        return DeviceInfo(
            configuration_url=self.controller.api.get_config_url(),
            identifiers={
                (DOMAIN, f"{self.controller.unique_id}_{unique_suffix}"),
            },
            name=self._data["name"],
            manufacturer=MANUFACTURER,
            model=self.controller.model,
            sw_version=self.controller.version,
            via_device=(DOMAIN, self.controller.unique_id),
        )
