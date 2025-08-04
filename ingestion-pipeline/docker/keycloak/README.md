# Keycloak Fine-Grained Access Control Documentation

This directory contains comprehensive documentation for implementing fine-grained access control (FGAC) for Apache Iceberg tables using Keycloak, OpenFGA, and Lakekeeper.

## 📚 Documentation Overview

### 🎯 Main Tutorial
- **[Fine-Grained Access Control Tutorial](README-Fine-Grained-Access-Control.md)** - Complete step-by-step guide for implementing FGAC

### 📖 Practical Examples
- **[Example User Setup](example-user-setup.md)** - Hands-on example of creating user "jane" with limited access

### ⚡ Quick Reference
- **[Quick Reference Guide](quick-reference.md)** - Common commands and operations for daily use

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

### 3. Create a New User
Follow the [Example User Setup](example-user-setup.md) to create user "jane" with limited access.

### 4. Test Access Control
Use the provided notebooks to test column-level access control.

## 🔐 Key Concepts

### Authentication (Keycloak)
- **Purpose**: User identity verification
- **Features**: User management, client registration, token issuance
- **Integration**: OAuth2/OpenID Connect protocol

### Authorization (OpenFGA)
- **Purpose**: Fine-grained permission decisions
- **Features**: Column-level, row-level, time-based access control
- **Model**: Declarative authorization language

### Catalog Management (Lakekeeper)
- **Purpose**: Apache Iceberg catalog with access control
- **Features**: Query enforcement, permission validation
- **Integration**: Consults OpenFGA for authorization decisions

## 📊 Access Control Levels

### 1. Column-Level Security
```fga
type id_column
  relations
    define can_read: [user:jane, user:service-account-trino]

type amount_column
  relations
    define can_read: [user:jane, user:service-account-trino]

type source_column
  relations
    define can_read: [user:service-account-trino]  # jane cannot access
```

### 2. Row-Level Security
```fga
type fake_seclink_row
  relations
    define can_read: [user:jane] if user.department = row.department
```

### 3. Time-Based Access
```fga
type time_based_access
  relations
    define can_read: [user] if current_time >= start_time and current_time <= end_time
```

## 👥 User Types

### Service Accounts
- **trino**: Full access to all columns
- **starrocks**: Full access to all columns  
- **duckdb**: Full access to all columns

### Limited Users
- **jane**: Access to ID and Amount columns only
- **irisa**: Access to ID and Amount columns only
- **Custom users**: Configurable column-level access

## 🔧 Configuration Files

### Keycloak Configuration
- **realm.json**: Complete realm configuration
- **Users**: Pre-configured users with different access levels
- **Clients**: OAuth2 clients for authentication
- **Scopes**: Custom scopes for fine-grained control

### OpenFGA Configuration
- **Authorization Models**: Define permission relationships
- **Tuples**: Specific authorization rules
- **Deployment Scripts**: Automated setup and configuration

## 🧪 Testing

### Test Notebooks
- **03-01-DuckDB.ipynb**: Full access testing
- **03-02-Trino.ipynb**: Full access testing
- **03-03-Starrocks.ipynb**: Full access testing
- **03-04-Irisa-Limited-Access.ipynb**: Limited access testing

### Test Scenarios
1. **Full Access**: Service accounts can access all columns
2. **Limited Access**: Users can only access permitted columns
3. **Access Denied**: Users are blocked from unauthorized columns
4. **Token Validation**: JWT token verification and expiration

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
   - Verify OpenFGA tuples
   - Check user permissions
   - Validate authorization model

3. **Service Connectivity**
   - Check Docker container status
   - Verify network connectivity
   - Review service logs

### Debug Commands
See [Quick Reference Guide](quick-reference.md) for detailed debugging commands.

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

**Note**: This documentation assumes you have Docker and Docker Compose installed and are familiar with basic concepts of authentication and authorization. 