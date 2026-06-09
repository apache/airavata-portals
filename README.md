# Apache Airavata Portals

The `airavata-portals` repository is a consolidated home for all web-based user interfaces built on top of the [Apache Airavata](https://airavata.apache.org/) middleware platform. This collection of frontend components and frameworks enables seamless interaction with Airavata's powerful orchestration, identity, data, and compute services.

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
