# Access Control with Lakekeeper and PyIceberg

This example demonstrates a comprehensive **Authentication and Authorization** setup for data lake management using modern cloud-native tools. The architecture provides secure access control for data operations across multiple query engines.

## 🏗️ Architecture Overview

This setup includes the following components:

### Core Services
- **Jupyter Notebooks** - Interactive development environment with Spark, PyIceberg, and data processing capabilities
- **Lakekeeper** - Data catalog and metadata management system
- **Keycloak** - Identity Provider (IdP) for authentication
- **OpenFGA** - Authorization backend for fine-grained access control
- **MinIO** - Object storage for data lake files

### Query Engines
- **Apache Spark** - Distributed computing engine
- **PyIceberg** - Python library for Apache Iceberg table format
- **Trino** - Distributed SQL query engine
- **StarRocks** - Real-time analytical database

### Database Layer
- **PostgreSQL** - Primary database for Lakekeeper metadata
- **OpenFGA Database** - Authorization policy storage

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 8GB of available RAM
- Ports 8889, 30080, 8181, 9000, 9001, 9999, 9030, 8030 available

### Running the Example

1. **Navigate to the docker directory:**
   ```bash
   cd docker
   ```

2. **Start all services:**
   ```bash
   docker compose -f compose-lakekeeper-pyiceberg-access-contrpl.yaml up -d
   ```

3. **Wait for all services to be healthy** (this may take 2-3 minutes on first run)

## 🌐 Access Points

Once all services are running, you can access the following interfaces:

| Service | URL | Description |
|---------|-----|-------------|
| **Jupyter Notebooks** | [http://localhost:8889](http://localhost:8889) | Interactive development environment |
| **Keycloak Admin** | [http://localhost:30080](http://localhost:30080) | Identity and access management |
| **Lakekeeper API** | [http://localhost:8181/swagger-ui/#/](http://localhost:8181/swagger-ui/#/) | REST API documentation |
| **Lakekeeper UI** | [http://localhost:8181](http://localhost:8181) | Web interface (use notebooks for setup) |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | Object storage management |
| **Trino** | [http://localhost:9999](http://localhost:9999) | SQL query interface |
| **StarRocks** | [http://localhost:8030](http://localhost:8030) | Analytics dashboard |

## 👤 User Accounts

### Pre-configured Users

#### Lakekeeper Users
- **Peter** (Admin user with full permissions)
  - Username: `peter`
  - Password: `iceberg`
  
- **Anna** (Regular user with no initial permissions)
  - Username: `anna`
  - Password: `iceberg`

#### Keycloak Admin
- **Administrator**
  - Username: `admin`
  - Password: `admin`
  - Realm: `iceberg` (pre-configured)

## 📚 Getting Started

### 1. Initial Setup
Follow the step-by-step instructions in the Jupyter notebook:
- **`02-01-Bootstrap.ipynb`** - Complete system initialization

### 2. Warehouse Creation
- **`02-02-Create-Warehouse.ipynb`** - Set up data warehouse structure

### 3. Query Engine Testing
Test different query engines with the provided notebooks:
- **`03-01-Spark.ipynb`** - Apache Spark operations
- **`03-02-Trino.ipynb`** - Trino SQL queries
- **`03-03-Starrocks.ipynb`** - StarRocks analytics
- **`03-04-PyIceberg.ipynb`** - PyIceberg table operations
- **`03-05-DuckDB.ipynb`** - DuckDB queries

## 🔐 Security Features

### Authentication
- **OAuth 2.0/OpenID Connect** via Keycloak
- **JWT tokens** for API access
- **Single Sign-On (SSO)** across all services

### Authorization
- **Fine-grained access control** via OpenFGA
- **Role-based permissions** for data access
- **Resource-level security** for tables, schemas, and warehouses

### Data Protection
- **Encrypted connections** between services
- **Secure token exchange** for service-to-service communication
- **Audit logging** for access tracking

## 🏢 Use Cases

This setup is ideal for:

- **Multi-tenant data platforms** with isolated user access
- **Enterprise data lakes** requiring strict access controls
- **Compliance-driven environments** (GDPR, HIPAA, etc.)
- **Research and development** with secure data sharing
- **Production analytics** with role-based data access

## 🔧 Configuration Details

### Environment Variables
Key configuration parameters are set in the Docker Compose file:
- Database connections and credentials
- OAuth/OIDC provider settings
- Authorization backend configuration
- Service discovery and networking

### Network Architecture
- **Isolated Docker network** (`iceberg_net`) for secure communication
- **Health checks** for all critical services
- **Dependency management** ensuring proper startup order

## 🚨 Important Notes

### Bootstrapping
⚠️ **Do not use the Lakekeeper UI for initial setup!** 
- Use the designated Jupyter notebook (`02-01-Bootstrap.ipynb`) instead
- The notebook ensures proper technical user configuration
- Manual UI setup may break the authentication flow

### Service Dependencies
- Services start in a specific order to ensure proper initialization
- Database migrations run automatically
- Authorization policies are loaded during startup

### Resource Requirements
- **Minimum RAM**: 8GB
- **Recommended RAM**: 16GB
- **Storage**: At least 10GB free space
- **CPU**: 4+ cores recommended

## 🛠️ Troubleshooting

### Common Issues

1. **Services not starting**
   - Check Docker logs: `docker compose logs [service-name]`
   - Ensure ports are not in use
   - Verify sufficient system resources

2. **Authentication failures**
   - Verify Keycloak is healthy
   - Check JWT token configuration
   - Ensure proper realm setup

3. **Authorization errors**
   - Confirm OpenFGA is running
   - Check policy configuration
   - Verify user permissions

### Useful Commands

```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs lakekeeper

# Restart specific service
docker compose restart lakekeeper

# Stop all services
docker compose down

# Clean up volumes (⚠️ removes all data)
docker compose down -v
```

## 📖 Advanced Usage

For more complex scenarios with shared query engines between users, see the **Access Control Advanced Example** which demonstrates:
- Cross-user query engine sharing
- Advanced permission models
- Multi-tenant isolation strategies

## 🤝 Contributing

This setup is part of the Iceberg Basic Tutorial. For questions or issues:
- Check the Jupyter notebooks for detailed explanations
- Review the service logs for debugging information
- Consult the Lakekeeper and OpenFGA documentation

---

**Happy Data Lake Management! 🏔️** 