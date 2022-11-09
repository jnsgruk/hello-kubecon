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
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus

logger = logging.getLogger(__name__)


class HelloKubeconCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.gosherve_pebble_ready, self._on_config_changed)
        self.framework.observe(self.on.pull_site_action, self._pull_site_action)

        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self._external_hostname,
                "service-name": self.app.name,
                "service-port": 8080,
            },
        )

    @property
    def _external_hostname(self):
        """Return the external hostname to be passed to ingress via the relation."""
        # It is recommended to default to `self.app.name` so that the external
        # hostname will correspond to the deployed application name in the
        # model, but allow it to be set to something specific via config.
        return self.config["external-hostname"] or self.app.name

    def _on_install(self, _):
        # Download the site
        self._fetch_site()

    def _on_config_changed(self, event):
        """Handle the config-changed event"""
        # Get the gosherve container so we can configure/manipulate it
        container = self.unit.get_container("gosherve")
        # Create a new config layer
        layer = self._gosherve_layer()

        if container.can_connect():
            # Get the current config
            services = container.get_plan().to_dict().get("services", {})
            # Check if there are any changes to services
            if services != layer["services"]:
                # Changes were made, add the new layer
                container.add_layer("gosherve", layer, combine=True)
                logging.info("Added updated layer 'gosherve' to Pebble plan")
                # Restart it and report a new status to Juju
                container.restart("gosherve")
                logging.info("Restarted gosherve service")
            # All is well, set an ActiveStatus
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("waiting for Pebble in workload container")

        self.ingress.update_config({"service-hostname": self._external_hostname})

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

    def _fetch_site(self):
        """Fetch latest copy of website from Github and move into webroot"""
        # Set the site URL
        site_src = "https://jnsgr.uk/demo-site"
        # Set some status and do some logging
        self.unit.status = MaintenanceStatus("Fetching web site")
        logger.info("Downloading site from %s", site_src)
        # Download the site
        urllib.request.urlretrieve(site_src, "/srv/index.html")
        # Set the unit status back to Active
        self.unit.status = ActiveStatus()

    def _pull_site_action(self, event):
        """Action handler that pulls the latest site archive and unpacks it"""
        self._fetch_site()
        event.set_results({"result": "site pulled"})


if __name__ == "__main__":
    main(HelloKubeconCharm)
