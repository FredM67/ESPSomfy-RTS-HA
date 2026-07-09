"""ESPSomfy parent entity class."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .controller import ESPSomfyController


class ESPSomfyEntity(CoordinatorEntity[ESPSomfyController], Entity):
    """Base entity for the ESPSomfy controller."""

    def __init__(self, *, data: Any, controller: ESPSomfyController) -> None:
        """Initialize the entity."""
        super().__init__(coordinator=controller)
        self.controller = controller

    @property
    def should_poll(self) -> bool:
        """Indicates that the entity should not poll."""
        return False

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
    """Base entity for ESPSomfy shades."""

    def __init__(self, *, data: Any, controller: ESPSomfyController) -> None:
        """Initialize the entity."""
        super().__init__(data=data, controller=controller)
        self._data = data

    @property
    def device_info(self) -> DeviceInfo | None:
        """Device info."""
        if "shadeId" in self._data:
            unique_suffix = f"shade_{self._data['shadeId']}"
        else:
            unique_suffix = f"group_{self._data['groupId']}"
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
