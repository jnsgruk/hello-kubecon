#!/usr/bin/env python3
# Copyright 2021 Jon Seager
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class HelloKubeconCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the gosherve container so we can configure/manipulate it
        container = self.unit.get_container("gosherve")
        # Create a new config layer
        layer = self._gosherve_layer()
        # Get the current config
        plan = container.get_plan()
        # Check if there are any changes to services
        if plan.services != layer["services"]:
            # Changes were made, add the new layer
            container.add_layer("gosherve", layer, combine=True)
            logging.info("Added updated layer 'gosherve' to Pebble plan")
            # Stop the service if it is already running
            if container.get_service("gosherve").is_running():
                container.stop("gosherve")
            # Restart it and report a new status to Juju
            container.start("gosherve")
            logging.info("Restarted gosherve service")
        # All is well, set an ActiveStatus
        self.unit.status = ActiveStatus()

    def _gosherve_layer(self):
        """Returns a Pebble configration layer for Gosherve"""
        return {
            "summary": "gosherve layer",
            "description": "pebble config layer for gosherve",
            "services": {
                "gosherve": {
                    "override": "replace",
                    "summary": "gosherve",
                    "command": "/gosherve",
                    "startup": "enabled",
                    "environment": {
                        "REDIRECT_MAP_URL": self.config["redirect-map"]
                    },
                }
            },
        }


if __name__ == "__main__":
    main(HelloKubeconCharm)
