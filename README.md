# Apache Airavata Portals

The `airavata-portals` repository is a consolidated home for all web-based user interfaces built on top of the [Apache Airavata](https://airavata.apache.org/) middleware platform. This collection of frontend components and frameworks enables seamless interaction with Airavata's powerful orchestration, identity, data, and compute services.

## Repository Structure

This repository contains the following sub-projects and templates:

### Modern Portals

- **airavata-research-portal** ⭐  
  Modern React/TypeScript portal with Spring Boot API backend. Features comprehensive resource management, search functionality, and clean UI design.

- **airavata-django-portal**  
  The reference Django-based web interface for Airavata services, supporting job submissions, project management, and monitoring.

- **airavata-django-portal-sdk**  
  A pluggable SDK enabling custom Django-based science gateways with minimal setup.

- **airavata-django-portal-commons**  
  Shared UI components and utilities used across Django-based portals.

- **airavata-custos-portal**  
  Vue.js-based UI for managing Custos identity, group, and resource permissions.

### Starter Templates

- **airavata-cookiecutter-django-app**  
  Cookiecutter template to scaffold new Django apps for integration with the Django portal.

- **airavata-cookiecutter-django-output-view**  
  Template for building reusable output viewers compatible with portal job results.

### Additional Components

- **airavata-local-agent**  
  Electron-based desktop application for local compute resource management.

- **airavata-mft-portal**  
  Django portal for Managed File Transfer services.

- **airavata-php-gateway**  
  Legacy PHP-based science gateway frontend (archived/deprecated).

## Quick Start - Research Portal

The **airavata-research-portal** is the modern flagship portal. To get started:

### Prerequisites
- Node.js 19+
- Java 11+
- Gradle

### Development Setup

**Terminal 1 - Start API Server:**
```bash
cd admin-api-server
./gradlew bootRun
# Server starts on http://localhost:8080
```

**Terminal 2 - Start React Portal:**
```bash
cd airavata-portals/airavata-research-portal
npm install
npm run dev
# Portal starts on http://localhost:5173
```

### API Endpoints

The Spring Boot backend provides REST endpoints for:

```
# Entity Management
GET    /api/{type}              # List all (models, datasets, notebooks, etc.)
GET    /api/{type}/{id}         # Get individual entity details  
POST   /api/{type}              # Create new entity
GET    /api/{type}/search?keyword={query}  # Search entities

# Resource Types: models, datasets, notebooks, repositories, storage-resources, compute-resources
```

### File Structure

```
airavata-research-portal/
├── src/
│   ├── components/          # React components organized by feature
│   │   ├── models/         # Model listing, detail, and forms
│   │   ├── datasets/       # Dataset components
│   │   ├── notebooks/      # Notebook components  
│   │   ├── repositories/   # Repository components
│   │   ├── resources/      # Storage/compute resource management
│   │   ├── search/         # Cross-entity search functionality
│   │   └── common/         # Shared UI components
│   ├── layouts/            # Page layouts and navigation
│   ├── lib/               # API services and utilities
│   └── App.tsx            # Main routing configuration

admin-api-server/
├── src/main/java/org/apache/airavata/admin_api_server/
│   ├── controller/        # REST API endpoints
│   ├── service/          # Business logic layer
│   ├── repository/       # Data access layer  
│   ├── entity/           # JPA entities
│   └── config/           # Configuration and data initialization
```

## Purpose

The goal of this consolidation is to:

- Simplify the discovery and contribution process for Airavata frontend components.
- Encourage reuse of UI components through a shared ecosystem.
- Promote rapid prototyping and customization of science gateways.
- Align documentation and tooling across related UI projects.
