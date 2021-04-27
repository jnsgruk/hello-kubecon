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
import urllib

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus

logger = logging.getLogger(__name__)

STORAGE_PATH = "/var/lib/juju/storage/webroot/0"
SITE_SRC = "https://jnsgr.uk/demo-site"


class HelloKubeconCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.pull_site_action, self._pull_site_action)

        self.ingress = IngressRequires(self, {
            "service-hostname": "hellokubecon.juju",
            "service-name": self.app.name,
            "service-port": 8080
        })

    def _on_install(self, _):
        # Download the site
        self._fetch_site()

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the gosherve container so we can configure/manipulate it
        container = self.unit.get_container("gosherve")
        # Do not continue if the configuration is incomplete
        if not self._check_config():
            return

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
                        "REDIRECT_MAP_URL": self.config["redirect-map"],
                        "WEBROOT": "/srv",
                    },
                }
            },
        }

    def _check_config(self):
        """Check that everything is in place to start Gosherve"""
        if not self.config["redirect-map"]:
            logger.warning("Cannot start Gosherve without 'redirect-map' configuration")
            self.unit.status = BlockedStatus("No 'redirect-map' config specified")
            return False
        return True

    def _fetch_site(self):
        """Fetch latest copy of website from Github and move into webroot"""
        # Set some status and do some logging
        self.unit.status = MaintenanceStatus("Fetching web site")
        logger.info("Downloading site from %s", SITE_SRC)
        # Download the site
        urllib.request.urlretrieve(SITE_SRC, f"{STORAGE_PATH}/index.html")
        # Set the unit status back to Active
        self.unit.status = ActiveStatus()

    def _pull_site_action(self, event):
        """Action handler that pulls the latest site archive and unpacks it"""
        self._fetch_site()
        event.set_results({"result": "site pulled"})


if __name__ == "__main__":
    main(HelloKubeconCharm)
