# Apache Airavata Portals

The `airavata-portals` repository is a consolidated home for all web-based user interfaces built on top of the [Apache Airavata](https://airavata.apache.org/) middleware platform. This collection of frontend components and frameworks enables seamless interaction with Airavata's powerful orchestration, identity, data, and compute services.

## Running locally with Tilt

The Django portal runs as a container tenant on the shared `airavata-devstack`
substrate (one colima VM, one Traefik ingress serving `*.airavata.host`), managed
with [Tilt](https://tilt.dev). The two stacks run as separate Tilt instances.

### One-time setup

```bash
# From either repo — both carry the identical devstack kit
./devstack/devstack setup
```

This installs colima, mkcert, dnsmasq, creates the shared VM and Traefik ingress,
and configures wildcard DNS for `*.airavata.host` → `127.0.0.1` (trusted cert, no `-k`).

### Daily startup

```bash
# 1. Start the Airavata backend stack (in the apache/airavata repo)
cd ../airavata && tilt up

# 2. Start the portals (this repo) on a distinct Tilt port
tilt up --port 10351
```

The Django portal is then served at **https://gateway.airavata.host** (trusted
HTTPS via the shared Traefik ingress). The portal runs inside the shared colima VM
as a container; `settings_local.py` is generated automatically on first `tilt up`
if the file does not exist. Only the Django portal is wired into the Tiltfile today;
other portals can be added as additional resources later.

### Log in and run your first experiment (Echo)

The backend stack seeds a ready-to-use tenant outside the JVM when its database is first
created — directly from SQL, before the server starts (default gateway, SFTP storage, a
docker-SLURM compute resource with a `normal` queue, the **Echo** application, and a
**Default Project**, all shared with `default-admin`). So once both stacks are green you can
run an experiment with zero manual setup:

1. Open **https://gateway.airavata.host** and log in as **`default-admin`** / **`ade4#21242ftfd`**.
2. Create an experiment: choose the **Echo** application, the **Default Project**, and the
   **slurm** compute resource (queue `normal`). The `Input_to_Echo` field defaults to
   `Hello, Airavata!`.
3. Launch it — it runs on the docker-SLURM cluster (env setup → `sbatch` over SSH → `sacct`
   monitoring → SFTP output staging) and reaches **COMPLETED**, with `Echo.stdout` holding
   the echoed input.

`tilt down` then `tilt up` brings the same working state back up (the database volume
persists); `./devstack/devstack reset` (or wiping the `db_data` volume) re-seeds it from scratch.

## Repository Structure

This repository contains the following sub-projects and templates:

### Portals and SDKs

- **airavata-django-portal**  
  The reference web-based user interface for interacting with Airavata services, supporting job submissions, project management, and monitoring. Talks to Airavata over gRPC via the `airavata-python-sdk`.

### Starter Templates

- **airavata-cookiecutter-django-app**  
  Cookiecutter template to scaffold new Django apps for integration with the Django portal.

- **airavata-cookiecutter-django-output-view**  
  Template for building reusable output viewers compatible with portal job results.

### Legacy and Other Frontends

- **airavata-php-gateway**  
  Legacy PHP-based science gateway frontend (archived/deprecated).

- **airavata-custos-portal**  
  Web-based UI for managing Custos identity, group, and resource permissions.

## Purpose

The goal of this consolidation is to:

- Simplify the discovery and contribution process for Airavata frontend components.
- Encourage reuse of UI components through a shared ecosystem.
- Promote rapid prototyping and customization of science gateways.
- Align documentation and tooling across related UI projects.
