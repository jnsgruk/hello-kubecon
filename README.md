## Kubecon Demonstration Charm

This charm is a demonstration of the new Sidecar Charm pattern for Juju 2.9. It uses [Pebble](https://github.com/canonical/pebble) and the [Python Operator Framework](https://pythonoperatorframework.io). It deploys a copy of [gosherve](https://github.com/jnsgruk/gosherve) and relies upon the sidecar container to populate a shared volume with web files.

Overview of features:

- Deploy a container running [gosherve](https://github.com/jnsgruk/gosherve)
- Charm container fetches a zip archive of a website [from Github](https://jnsgr.uk/demo-site-repo)
- Charm container puts the contents of the archive in a storage volume
- Once a `redirect-map` config item is set, `gosherve` is started
- There is a `pull-site` action which will pull the latest version of the test site and extract it
- Ingress relation is implemented and creates a hostname "hellokubecon.juju"
- Since we're deploying on microk8s we set the ingress-class to "public"

Each branch of this repository represents a different stage from the demonstration:

- [`1-specify-workload`](https://github.com/jnsgruk/hello-kubecon/tree/1-specify-workload)
- [`2-handle-configuration`](https://github.com/jnsgruk/hello-kubecon/tree/2-handle-configuration)
- [`3-basic-storage`](https://github.com/jnsgruk/hello-kubecon/tree/3-basic-storage)
- [`4-kubecon-site`](https://github.com/jnsgruk/hello-kubecon/tree/4-kubecon-site)
- [`5-action`](https://github.com/jnsgruk/hello-kubecon/tree/5-action)
- [`6-ingress`](https://github.com/jnsgruk/hello-kubecon/tree/6-ingress)
- [`master`](https://github.com/jnsgruk/hello-kubecon/)

### Getting Started

To build it locally. To setup a local test environment with [MicroK8s](https://microk8s.io), do the following:

```bash
$ sudo snap install --classic microk8s
$ sudo usermod -aG microk8s $(whoami)
$ sudo microk8s enable storage dns
$ sudo snap alias microk8s.kubectl kubectl
$ newgrp microk8s
```

Next install Charmcraft and build the Charm

```bash
# Install Charmcraft
$ sudo snap install charmcraft --edge
# Clone an example charm
$ git clone https://github.com/jnsgruk/hello-kubecon
# Build the charm
$ cd hello-kubecon
$ charmcraft build
```

Now you're ready to deploy the Charm:

```bash
# For now, we require the 2.9/edge channel until features land in candidate/stable
$ sudo snap refresh juju --channel=2.9/edge
# Create a model for our deployment
$ juju add-model kubecon
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

You should be able to visit http://hellokubecon.juju in your browser.
