# Copyright 2021 Jon Seager
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock, patch

from charm import HelloKubeconCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(HelloKubeconCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_gosherve_layer(self):
        # Test with empty config.
        self.assertEqual(self.harness.charm.config["redirect-map"], "https://jnsgr.uk/demo-routes")
        expected = {
            "summary": "gosherve layer",
            "description": "pebble config layer for gosherve",
            "services": {
                "gosherve": {
                    "override": "replace",
                    "summary": "gosherve",
                    "command": "/gosherve",
                    "startup": "enabled",
                    "environment": {
                        "REDIRECT_MAP_URL": "https://jnsgr.uk/demo-routes",
                        "WEBROOT": "/srv",
                    },
                }
            },
        }
        self.assertEqual(self.harness.charm._gosherve_layer(), expected)
        # And now test with a different value in the redirect-map config option.
        # Disable hook firing first.
        self.harness.disable_hooks()
        self.harness.update_config({"redirect-map": "test value"})
        expected["services"]["gosherve"]["environment"]["REDIRECT_MAP_URL"] = "test value"
        self.assertEqual(self.harness.charm._gosherve_layer(), expected)

    def test_on_config_changed(self):
        plan = self.harness.get_container_pebble_plan("gosherve")
        self.assertEqual(plan.to_dict(), {})
        # Trigger a config-changed hook. Since there was no plan initially, the
        # "gosherve" service in the container won't be running so we'll be
        # testing the `is_running() == False` codepath.
        self.harness.update_config({"redirect-map": "test value"})
        plan = self.harness.get_container_pebble_plan("gosherve")
        # Get the expected layer from the gosherve_layer method (tested above)
        expected = self.harness.charm._gosherve_layer()
        expected.pop("summary", "")
        expected.pop("description", "")
        # Check the plan is as expected
        self.assertEqual(plan.to_dict(), expected)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
        container = self.harness.model.unit.get_container("gosherve")
        self.assertEqual(container.get_service("gosherve").is_running(), True)

        # Now test again with different config, knowing that the "gosherve"
        # service is running (because we've just tested it above), so we'll
        # be testing the `is_running() == True` codepath.
        # We also want to confirm logging here, because later on we're using
        # lack of logging to confirm different behaviour.
        with self.assertLogs(level='INFO') as logger:
            self.harness.update_config({"redirect-map": "test2 value"})
        expected_logs = [
            "INFO:root:Added updated layer 'gosherve' to Pebble plan",
            "INFO:root:Restarted gosherve service",
        ]
        self.assertEqual(sorted(logger.output), expected_logs)
        plan = self.harness.get_container_pebble_plan("gosherve")
        # Adjust the expected plan
        expected["services"]["gosherve"]["environment"]["REDIRECT_MAP_URL"] = "test2 value"
        self.assertEqual(plan.to_dict(), expected)
        self.assertEqual(container.get_service("gosherve").is_running(), True)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        # And finally test again with the same config to ensure we exercise
        # the case where the plan we've created matches the active one. We're
        # asserting that we raise an error here because there are no logs of
        # level INFO or higher. This is a proxy for confirming we're not adding
        # a pebble layer or restarting the service, as we log those things.
        with self.assertRaises(AssertionError):
            with self.assertLogs(level='INFO'):
                self.harness.charm.on.config_changed.emit()

    @patch("charm.HelloKubeconCharm._fetch_site")
    def test_on_install(self, _fetch_site):
        self.harness.charm._on_install("mock_event")
        _fetch_site.assert_called_once

    @patch("charm.HelloKubeconCharm._fetch_site")
    def test_pull_site_action(self, _fetch_site):
        mock_event = Mock()
        self.harness.charm._pull_site_action(mock_event)
        _fetch_site.assert_called_once
        mock_event.called_once_with({"result": "site pulled"})
