# Keycloak Fine-Grained Access Control Documentation

This directory contains comprehensive documentation for implementing fine-grained access control (FGAC) for Apache Iceberg tables using Keycloak, OpenFGA, and Lakekeeper.

## 📚 Documentation Overview

### 🎯 Core Documentation
- **[Keycloak Concepts and Realm Configuration](Keycloak-Concepts-and-Realm-Explanation.md)** - Comprehensive explanation of Keycloak concepts and realm.json structure
- **[How-To: User Management and Table Permissions](How-To-User-Management-and-Permissions.md)** - Step-by-step guide for adding users and setting permissions
- **[Keycloak-OpenFGA Integration](Keycloak-OpenFGA-Integration.md)** - Comprehensive guide to integrating Keycloak and OpenFGA

### 🔧 Configuration Files
- **[realm.json](realm.json)** - Keycloak realm configuration with users, clients, and scopes
- **[OpenFGA Models](../openfga/)** - Authorization models and tuples for fine-grained control

## 🏗️ Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  Keycloak   │───▶│   OpenFGA   │───▶│  Lakekeeper │
│ (Trino/DB)  │    │ (Auth)      │    │ (Authz)     │    │ (Catalog)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                               │
                                                               ▼
                                                     ┌─────────────┐
                                                     │ Iceberg     │
                                                     │ Tables      │
                                                     └─────────────┘
```

### Component Responsibilities

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **Keycloak** | Authentication & Identity Management | User management, JWT token issuance, OAuth2/OpenID Connect |
| **OpenFGA** | Fine-Grained Authorization | Column-level permissions, row-level security, dynamic access control |
| **Lakekeeper** | Catalog Management | Apache Iceberg catalog with access control enforcement |
| **Apache Iceberg** | Data Storage | ACID transactions, schema evolution, time travel |

## 🚀 Quick Start

### 1. Start Services
```bash
cd ingestion-pipeline/docker
docker-compose -f compose-lakekeeper-pyiceberg-access-control.yaml up -d
```

### 2. Access Keycloak Admin Console
- **URL**: `http://localhost:30080`
- **Username**: `admin`
- **Password**: `admin`
- **Realm**: `iceberg`

### 3. Deploy Authorization Model
```bash
cd docker/openfga
chmod +x deploy-simple.sh
./deploy-simple.sh
```

### 4. Create a New User
Follow the [How-To: User Management and Table Permissions](How-To-User-Management-and-Permissions.md) to create users and set permissions.

### 5. Test Access Control
Use the provided notebooks to test column-level access control.

## 🔐 Key Concepts

### Authentication (Keycloak)
- **Purpose**: User identity verification and token management
- **Features**: 
  - User management and role assignment
  - OAuth2/OpenID Connect protocol support
  - JWT token issuance with custom claims
  - Service account management for machine-to-machine authentication
- **Integration**: Provides identity context to OpenFGA for authorization decisions

### Authorization (OpenFGA)
- **Purpose**: Fine-grained permission decisions and access control
- **Features**:
  - Column-level security (e.g., user can only access ID and Amount columns)
  - Row-level security (e.g., user can only access rows from their department)
  - Time-based access control
  - Dynamic permission evaluation
- **Model**: Declarative authorization language with relationship-based permissions

### Catalog Management (Lakekeeper)
- **Purpose**: Apache Iceberg catalog with integrated access control
- **Features**:
  - Query enforcement and permission validation
  - Integration with OpenFGA for authorization decisions
  - Support for multiple query engines (Trino, StarRocks, DuckDB)
  - ACID transaction support

## 📊 Access Control Levels

### 1. Column-Level Security
```json
{
  "type": "id_column",
  "relations": {
    "can_read": {
      "directly_related_user_types": [
        { "type": "user", "id": "jane" },
        { "type": "user", "id": "service-account-trino" },
        { "type": "user", "id": "service-account-starrocks" },
        { "type": "user", "id": "service-account-duckdb" }
      ]
    }
  }
}
```

### 2. Row-Level Security
```json
{
  "type": "fake_seclink_row",
  "relations": {
    "can_read": {
      "directly_related_user_types": [
        { "type": "user", "id": "jane" }
      ]
    }
  }
}
```

### 3. Time-Based Access
```json
{
  "type": "time_based_access",
  "relations": {
    "can_read": {
      "directly_related_user_types": [
        { "type": "user" }
      ]
    }
  }
}
```

### 4. Dynamic Permissions
```json
{
  "type": "dynamic_permission",
  "relations": {
    "can_read": {
      "directly_related_user_types": [
        { "type": "user" }
      ]
    }
  }
}
```

## 👥 User Types and Access Levels

### Service Accounts (Full Access)
| Service Account | Purpose | Access Level |
|-----------------|---------|--------------|
| `service-account-trino` | Trino query engine | Full access to all columns |
| `service-account-starrocks` | StarRocks query engine | Full access to all columns |
| `service-account-duckdb` | DuckDB query engine | Full access to all columns |

### Limited Users (Column-Level Access)
| User | Purpose | Access Level | Accessible Columns |
|------|---------|--------------|-------------------|
| `jane` | Data analyst | Limited | ID, Amount only |
| `irisa` | Business user | Limited | ID, Amount only |
| Custom users | Configurable | Variable | Based on role assignment |

### Access Matrix for `fake_seclink` Table

| User | ID | Amount | Source | Destination | DateIn | DateOut | Message |
|------|----|--------|--------|-------------|--------|---------|---------|
| `jane` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `irisa` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `service-account-trino` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `service-account-starrocks` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `service-account-duckdb` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## 🔧 Configuration Files

### Keycloak Configuration
- **realm.json**: Complete realm configuration with users, clients, and scopes
- **Users**: Pre-configured users with different access levels
- **Clients**: OAuth2 clients for authentication
- **Scopes**: Custom scopes for fine-grained control

### OpenFGA Configuration
- **jane-limited-access-model.json**: Authorization model definition
- **jane-limited-access-tuples.json**: Authorization tuples for column-level access
- **deploy-simple.sh**: Automated deployment script

## 🧪 Testing and Validation

### Test Notebooks
- **03-01-DuckDB.ipynb**: Full access testing with DuckDB
- **03-02-Trino.ipynb**: Full access testing with Trino
- **03-03-Starrocks.ipynb**: Full access testing with StarRocks
- **03-04-Irisa-Limited-Access.ipynb**: Limited access testing

### Test Scenarios
1. **Full Access**: Service accounts can access all columns
2. **Limited Access**: Users can only access permitted columns
3. **Access Denied**: Users are blocked from unauthorized columns
4. **Token Validation**: JWT token verification and expiration handling

### Manual Testing Commands
```bash
# Test jane's limited access
curl -X POST http://lakekeeper:8181/catalog/query \
  -H "Authorization: Bearer $JANE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT ID, Amount FROM irisa.fake_seclink LIMIT 5"}'

# Test access denial
curl -X POST http://lakekeeper:8181/catalog/query \
  -H "Authorization: Bearer $JANE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT ID, Amount, Source FROM irisa.fake_seclink LIMIT 5"}'
```

## 🔍 Monitoring and Debugging

### Service Health Checks
```bash
# Keycloak
curl http://keycloak:8080/health

# OpenFGA
curl http://openfga:8080/healthz

# Lakekeeper
curl http://lakekeeper:8181/health
```

### Log Monitoring
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f keycloak openfga lakekeeper
```

### Authorization Testing
```bash
# Test OpenFGA authorization
curl -X POST http://openfga:8080/stores/$STORE_ID/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "tuple_key": {
      "user": "user:jane",
      "relation": "can_read",
      "object": "id_column:irisa.fake_seclink.id"
    }
  }'
```

## 🚨 Troubleshooting

### Common Issues

1. **Token Expiration**
   - Check token expiration time
   - Refresh tokens before expiration
   - Use appropriate token lifespan

2. **Authorization Denied**
   - Verify OpenFGA tuples are deployed
   - Check user permissions in authorization model
   - Validate authorization model is active

3. **Service Connectivity**
   - Check Docker container status
   - Verify network connectivity
   - Review service logs

### Debug Commands
See [How-To: User Management and Table Permissions](How-To-User-Management-and-Permissions.md) for detailed debugging commands and troubleshooting steps.

## 📈 Performance Considerations

### Optimization Tips
- Cache authorization decisions
- Use efficient OpenFGA queries
- Monitor authorization latency
- Implement connection pooling

### Scaling
- Horizontal scaling for high availability
- Load balancing for multiple instances
- Database optimization for large datasets

## 🔒 Security Best Practices

### Authentication
- Use strong passwords
- Implement password policies
- Regular password rotation
- Multi-factor authentication (MFA)

### Authorization
- Principle of least privilege
- Regular permission audits
- Secure token handling
- Access logging and monitoring

### Infrastructure
- Network segmentation
- TLS encryption
- Regular security updates
- Backup and recovery procedures

## 📚 Additional Resources

### Documentation
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenFGA Documentation](https://openfga.dev/docs)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [Lakekeeper Documentation](https://lakekeeper.io/docs)

### Community
- [Keycloak Community](https://www.keycloak.org/community)
- [OpenFGA Community](https://openfga.dev/community)
- [Apache Iceberg Community](https://iceberg.apache.org/community/)

## 🤝 Contributing

To contribute to this documentation:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This documentation is provided under the same license as the main project.

---

**Note**: This documentation assumes you have Docker and Docker Compose installed and are familiar with basic concepts of authentication and authorization. For detailed step-by-step instructions, refer to the [How-To: User Management and Table Permissions](How-To-User-Management-and-Permissions.md). 