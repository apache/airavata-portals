# Apache Airavata Research Portal

A modern React-based portal for the Apache Airavata middleware platform, providing a comprehensive interface for managing computational resources, datasets, models, notebooks, and repositories.

## 🏗️ Architecture Overview

### Frontend Stack
- **React 19** with TypeScript
- **Vite** build tool for fast development
- **Chakra UI v3** for consistent component design
- **React Router v7** for navigation
- **Axios** for API communication

### Backend Integration
- **Spring Boot 3.5.3** Admin API Server
- **H2 Database** (in-memory for development)
- **JPA/Hibernate** for data persistence
- **Clean Architecture** with repository pattern

## 🚀 Quick Start

### Prerequisites
- Node.js 19+ 
- Java 17+
- Spring Boot Admin API Server running on port 8080

### Development Setup

1. **Clone and navigate to the project**
   ```bash
   cd airavata-portals/airavata-research-portal
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Fill in the .env file with development values
   ```

4. **Start the Admin API Server** (in separate terminal)
   ```bash
   cd admin-api-server
   ./gradlew bootRun
   ```
   Server will start on: http://localhost:8080

5. **Start the React development server**
   ```bash
   npm run dev
   ```
   Portal will start on: http://localhost:5173

### Production Build

1. **Create production environment file**
   ```bash
   cp .env.example .env.production
   # Configure production values
   ```

2. **Build for production**
   ```bash
   npm run build
   ```

3. **Start production server**
   ```bash
   npm run preview
   ```

## 📋 Features Implemented

### ✅ Core Functionality
- **Authentication**: OIDC integration with existing auth system
- **Navigation**: Global sidebar layout with Cybershuttle branding
- **Search**: Cross-entity search across models, datasets, notebooks, repositories
- **Resource Management**: Complete CRUD operations for all entities

### ✅ Entity Management

#### Models
- **Browse**: Filterable grid view with categories
- **Add New**: Simple form for creating ML models
- **Detail View**: Individual model information
- **API**: Full integration with `/api/models` endpoints

#### Datasets  
- **Browse**: Filterable grid view with categories
- **Add New**: Multi-step upload flow (File/URL/GitHub Repository)
- **Detail View**: Dataset information with file structure
- **API**: Full integration with `/api/datasets` endpoints

#### Resources (Storage & Compute)
- **Browse**: Tabbed interface for Storage/Compute resources
- **Add Storage**: S3/Cloud storage configuration form
- **Add Compute**: Host-based configuration with queue management
- **API**: Integration with `/api/storage-resources` and `/api/compute-resources`

#### Notebooks & Repositories
- **Browse**: Grid view with search and filtering
- **API**: Integration with respective endpoints

### ✅ Search & Discovery
- **Global Search**: Unified search across all entity types
- **Filtering**: Category-based and tag-based filtering
- **Popular Tags**: Dynamic tag suggestions
- **Results**: Categorized search results with type filtering

## 🔌 API Integration

### Base Configuration
```typescript
// Admin API Server
const ADMIN_API_BASE_URL = 'http://localhost:8080';

// Available endpoints
/api/models, /api/datasets, /api/notebooks, /api/repositories
/api/storage-resources, /api/compute-resources
/api/*/search?keyword={query}
```

### API Service Structure
```typescript
// lib/adminApi.ts
export const adminApiService = {
  // Models
  getModels(), createModel(), searchModels(), starModel(),
  
  // Datasets  
  getDatasets(), createDataset(), searchDatasets(), starDataset(),
  
  // Resources
  getStorageResources(), createStorageResource(),
  getComputeResources(), createComputeResource(),
  
  // Notebooks & Repositories
  getNotebooks(), searchNotebooks(), starNotebook(),
  getRepositories(), searchRepositories(), starRepository(),
};
```

## 📁 Project Structure

```
src/
├── components/
│   ├── auth/           # Authentication components
│   ├── common/         # Reusable components (ItemCard, etc.)
│   ├── datasets/       # Dataset management
│   │   ├── index.tsx           # Dataset listing
│   │   ├── AddDatasetForm.tsx  # Multi-step upload
│   │   └── DatasetDetail.tsx   # Detail view
│   ├── models/         # Model management
│   │   ├── index.tsx           # Model listing  
│   │   └── AddModelForm.tsx    # Simple model creation
│   ├── resources/      # Resource management
│   │   ├── index.tsx                    # Tabbed resource listing
│   │   ├── AddStorageResourceForm.tsx   # S3/Cloud storage
│   │   └── AddComputeResourceForm.tsx   # Host/Queue config
│   ├── search/         # Search functionality
│   │   └── SearchResults.tsx   # Cross-entity search
│   ├── layout/         # Layout components
│   └── home/           # Landing pages
├── lib/
│   ├── adminApi.ts     # API service layer
│   └── constants.ts    # Configuration constants
├── layouts/
│   └── SidebarLayout.tsx   # Main application layout
└── App.tsx             # Route configuration
```

## 🎨 UI Components & Patterns

### Chakra UI v3 Constraints
```typescript
// ❌ DO NOT USE (v3 compatibility issues)
Table, Card, Thead, Tbody, Tr, Th, Td

// ✅ USE ONLY
Box, VStack, HStack, Text, Button, Input, Badge, Container
```

### Component Patterns
```typescript
// ItemCard - Reusable entity card
<ItemCard 
  id={item.id} 
  title={item.title}
  description={item.description}
  tags={item.tags}
  authors={item.authors}
  starCount={item.starCount}
  onStar={handleStar}
/>

// Navigation-aware routing
const handleCardClick = () => {
  if (location.pathname.includes('/datasets')) {
    navigate(`/resources/datasets/${id}`);
  }
  // ... other entity types
};
```

## 🗄️ Database & Sample Data

### H2 Database (Development)
- **Console**: http://localhost:8080/h2-console
- **JDBC URL**: `jdbc:h2:mem:testdb`
- **Username**: `sa`, **Password**: (empty)

### Sample Data Categories
The DataInitializer populates diverse sample data:
- **Medical**: lung nodules, CT scans, healthcare data
- **Finance**: fraud detection, stock prediction, credit risk  
- **Cybersecurity**: malware detection, threat analysis
- **Life Sciences**: protein folding, bioinformatics
- **Computer Vision**: image classification, object detection
- **NLP**: sentiment analysis, text processing
- **Environmental**: climate modeling, weather prediction

## 🔍 Testing & Validation

### API Testing with Postman
```bash
# Health Check
GET http://localhost:8080/api/health

# Test Data
GET http://localhost:8080/api/test

# Entity Endpoints
GET http://localhost:8080/api/models
POST http://localhost:8080/api/models
GET http://localhost:8080/api/models/search?keyword=medical

# Headers
Content-Type: application/json
Accept: application/json
```

### Frontend Testing
```bash
# Development
npm run dev

# Build validation
npm run build
npm run preview

# Linting
npm run lint
```

## 🔧 Configuration

### Environment Variables
```bash
# .env or .env.production
VITE_ADMIN_API_BASE_URL=http://localhost:8080
VITE_CLIENT_ID=your-oidc-client-id
VITE_OPENID_CONFIG_URL=https://auth.dev.cybershuttle.org/.well-known/openid_configuration
VITE_APP_REDIRECT_URI=http://localhost:5173
```

### Build Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8080'
    }
  }
});
```

## 🚧 Current Implementation Status

### ✅ Completed Features
- Complete UI overhaul with clean design system
- Authentication system integration (preserved existing OIDC)
- All CRUD operations for Models, Datasets, Storage/Compute Resources
- Cross-entity search with filtering and categorization
- Navigation with global sidebar and routing
- API integration with comprehensive error handling

### ⚠️ Known Limitations
- H2 in-memory database (data resets on server restart)
- Basic file upload simulation (UI only)
- Simple queue configuration (needs advanced scheduling features)
- Search functionality works but could use advanced filtering

### 🎯 Next Steps for Implementation
1. **Production Database**: Replace H2 with PostgreSQL/MySQL
2. **File Upload**: Implement real file handling with cloud storage
3. **Advanced Queue Management**: Enhanced compute resource scheduling
4. **User Management**: Role-based access control
5. **Real-time Updates**: WebSocket integration for live status updates
6. **Advanced Search**: Elasticsearch integration for complex queries

## 📖 Usage Examples

### Adding a New Model
1. Navigate to `/resources/models`
2. Click "New Models" button
3. Fill in title and description
4. Click "Create Model"
5. Redirects to models listing with new entry

### Adding a Dataset
1. Navigate to `/resources/datasets` 
2. Click "New Dataset" button
3. Choose upload method (File/URL/Repository)
4. Fill in metadata and source details
5. Click "Create Dataset"

### Adding Compute Resources
1. Navigate to `/resources` → Compute tab
2. Click "+ Add Resource" button  
3. Fill in host configuration
4. Optionally add queue configuration
5. Click "Verify & Create"

## 🤝 Contributing

This is part of the Apache Airavata project. The implementation follows clean architecture principles with:
- **Separation of Concerns**: API layer, business logic, presentation
- **Type Safety**: Full TypeScript implementation
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Code Standards**: ESLint configuration and consistent patterns

## 📄 License

Licensed under the Apache License, Version 2.0. See the LICENSE file for details.

---

**Built with ❤️ for the Apache Airavata community**