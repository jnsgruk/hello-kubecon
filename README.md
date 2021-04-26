# Operator Day 2021 Demonstration Charm

- [Overview](#overview)
  - [Development Setup](#development-setup)
  - [Deploy](#deploy)
  - [Testing](#testing)
- [Get Help & Community](#get-help---community)
- [More Information/Related](#more-information-related)

## Overview

This charm is a demonstration of a charm implemeting the sidecar pattern used
during
[Operator Day 2021](https://www.linkedin.com/events/6788422954821656577/).
The charm is written using the
[Charmed Operator Framework](https://github.com/canonical/operator).
It deploys [gosherve](https://github.com/jnsgruk/gosherve), relying upon the
charm container to populate a shared volume with a simple landing-page style
website and configure the app before it is started.

Overview of charm features:

- Deploy a container running [gosherve](https://github.com/jnsgruk/gosherve)
- Fetch a zip archive of a website [from Github](https://jnsgr.uk/demo-site-repo)
- Place contents of the archive in a storage volume
- Expose a `redirect-map` config item to configure
  [gosherve](https://github.com/jnsgruk/gosherve) redirects
- Expose a `pull-site` action to pull the latest version of the test site
- Ingress relation is implemented using the
  [`nginx-ingress-integrator`](https://charmhub.io/nginx-ingress-integrator) library

Each branch of this repository represents a different stage from the demonstration:

- [`1-specify-workload`](https://github.com/jnsgruk/hello-kubecon/tree/1-specify-workload)
- [`2-handle-configuration`](https://github.com/jnsgruk/hello-kubecon/tree/2-handle-configuration)
- [`3-basic-storage`](https://github.com/jnsgruk/hello-kubecon/tree/3-basic-storage)
- [`4-kubecon-site`](https://github.com/jnsgruk/hello-kubecon/tree/4-kubecon-site)
- [`5-action`](https://github.com/jnsgruk/hello-kubecon/tree/5-action)
- [`6-ingress`](https://github.com/jnsgruk/hello-kubecon/tree/6-ingress)
- [`master`](https://github.com/jnsgruk/hello-kubecon/)

### Development Setup

To set up a local test environment with [MicroK8s](https://microk8s.io):

```bash
# Install MicroK8s
$ sudo snap install --classic microk8s
# Wait for MicroK8s to be ready
$ sudo microk8s status --wait-ready
# Enable features required by Juju controller & charm
$ sudo microk8s enable storage dns ingress
# (Optional) Alias kubectl bundled with MicroK8s package
$ sudo snap alias microk8s.kubectl kubectl
# (Optional) Add current user to 'microk8s' group
# This avoid needing to use 'sudo' with the 'microk8s' command
$ sudo usermod -aG microk8s $(whoami)
# Activate the new group (in the current shell only)
# Log out and log back in to make the change system-wide
$ newgrp microk8s
# Install Charmcraft
$ sudo snap install charmcraft --classic --edge
# Install juju
$ sudo snap install juju --classic --channel=2.9/candidate
# Bootstrap the Juju controller on MicroK8s
$ juju bootstrap microk8s micro
```

### Deploy

```bash
# Clone the charm code
$ git clone https://github.com/jnsgruk/hello-kubecon && cd hello-kubecon
# Build the charm package
$ charmcraft build
# Create a model for our deployment
$ juju add-model development
# Deploy!
$ juju deploy ./hello-kubecon.charm \
    --resource gosherve-image=jnsgruk/gosherve:latest \
    --config redirect-map="https://jnsgr.uk/demo-routes"
# Deploy the ingress integrator
$ juju deploy nginx-ingress-integrator
# Relate our app to the ingress
$ juju relate hello-kubecon nginx-ingress-integrator
# Set the ingress class
$ juju config nginx-ingress-integrator ingress-class="public"
# Add an entry to /etc/hosts
$ echo "127.0.1.1 hellokubecon.juju" | sudo tee -a /etc/hosts
# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

You should be able to visit [http://hellokubecon.juju](http://hellokubecon.juju)
in your browser.

### Testing

```bash
# Clone the charm code
$ git clone https://github.com/jnsgruk/hello-kubecon && cd hello-kubecon
# Install python3-virtualenv
$ sudo apt update && sudo apt install -y python3-virtualenv
# Create a virtualenv for the charm code
$ virtualenv venv
# Activate the venv
$ source ./venv/bin/activate
# Install dependencies
$ pip install -r requirements-dev.txt
# Run the tests
$ ./run_tests

```

## Get Help & Community

If you get stuck deploying this charm, or would like help with charming
generally, come and join the charming community!

- [Community Discourse](https://discourse.charmhub.io)
- [Community Chat](https://chat.charmhub.io/charmhub/channels/creating-charmed-operators)

## More Information/Related

Below are some links related to this demonstration:

- [Charmed Operator Framework Documentation](https://juju.is/docs/sdk)
- [Charmed Operator Framework Source](https://github.com/canonical/operator)
- [Juju Documentation](https://juju.is/docs/olm)
- [Charmhub](https://charmhub.io)
- [Pebble](https://github.com/canonical/github)
- [The Future of Charmed Operators on Kubernetes](https://discourse.charmhub.io/t/4361)
