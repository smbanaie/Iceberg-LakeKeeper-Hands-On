# Quick Reference Guide: Fine-Grained Access Control

This quick reference guide provides common commands and operations for managing fine-grained access control with Keycloak, OpenFGA, and Lakekeeper.

## 🚀 Quick Start Commands

### Start Services
```bash
# Start all services
docker-compose -f compose-lakekeeper-pyiceberg-access-control.yaml up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f keycloak openfga lakekeeper
```

### Access Keycloak Admin Console
- **URL**: `http://localhost:30080`
- **Username**: `admin`
- **Password**: `admin`
- **Realm**: `iceberg`

## 👤 User Management

### Add User via Keycloak UI
1. Go to **Users** → **Add user**
2. Fill in details:
   - Username: `newuser`
   - Email: `newuser@example.com`
   - First Name: `New`
   - Last Name: `User`
3. Set password in **Credentials** tab
4. Assign roles in **Role Mappings** tab

### Add User via JSON (realm.json)
```json
{
  "id": "user-id-$(date +%s)",
  "username": "newuser",
  "firstName": "New",
  "lastName": "User",
  "email": "newuser@example.com",
  "emailVerified": true,
  "enabled": true,
  "credentials": [
    {
      "type": "password",
      "value": "hashed-password",
      "temporary": false
    }
  ],
  "realmRoles": ["default-roles-iceberg"]
}
```

### Create Client for User
```json
{
  "clientId": "newuser-client",
  "name": "New User Client",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "NewUserSecret123",
  "serviceAccountsEnabled": true,
  "publicClient": false,
  "protocol": "openid-connect"
}
```

## 🔐 OpenFGA Operations

### Check OpenFGA Health
```bash
# Note: OpenFGA playground is disabled due to OIDC authentication
# Access OpenFGA API directly via internal network
curl http://openfga:8080/healthz
```

### Create Store
```bash
curl -X POST http://openfga:8080/stores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"my-store"}'
```

### List Stores
```bash
curl -X GET http://openfga:8080/stores \
  -H "Authorization: Bearer $TOKEN"
```

### Create Authorization Model
```bash
curl -X POST http://openfga:8080/stores/$STORE_ID/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @model.fga
```

### Write Tuples
```bash
curl -X POST http://openfga:8080/stores/$STORE_ID/authorization-models/$MODEL_ID/write \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @tuples.json
```

### Check Authorization
```bash
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

## 🔑 Token Management

### Get Client Credentials Token
```bash
curl -X POST http://keycloak:8080/realms/iceberg/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=trino" \
  -d "client_secret=AK48QgaKsqdEpP9PomRJw7l2T7qWGHdZ"
```

### Get User Token
```bash
curl -X POST http://keycloak:8080/realms/iceberg/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=trino" \
  -d "client_secret=AK48QgaKsqdEpP9PomRJw7l2T7qWGHdZ" \
  -d "username=jane" \
  -d "password=password123"
```

### Decode JWT Token
```bash
echo $TOKEN | jq -R 'split(".") | .[1] | @base64d | fromjson'
```

## 📊 Access Control Patterns

### Column-Level Access
```fga
type column
  relations
    define can_read: [user]
    define can_write: [user]

type id_column
  relations
    define can_read: [user:jane, user:service-account-trino]

type amount_column
  relations
    define can_read: [user:jane, user:service-account-trino]

type source_column
  relations
    define can_read: [user:service-account-trino]
```

### Row-Level Access
```fga
type row
  relations
    define can_read: [user]

type fake_seclink_row
  relations
    define can_read: [user:jane] if user.department = row.department
```

### Time-Based Access
```fga
type time_based_access
  relations
    define can_read: [user] if current_time >= start_time and current_time <= end_time
```

## 🧪 Testing Commands

### Test Lakekeeper Query
```bash
curl -X POST http://lakekeeper:8181/catalog/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT ID, Amount FROM irisa.fake_seclink LIMIT 5"}'
```

### Test OpenFGA Authorization
```bash
# Check if user can read specific column
curl -X POST http://openfga:8080/stores/$STORE_ID/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "tuple_key": {
      "user": "user:jane",
      "relation": "can_read",
      "object": "amount_column:irisa.fake_seclink.amount"
    }
  }'
```

### Test Token Validity
```bash
curl -X POST http://keycloak:8080/realms/iceberg/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Troubleshooting

### Check Service Status
```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps keycloak openfga lakekeeper
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs keycloak
docker-compose logs openfga
docker-compose logs lakekeeper

# Follow logs
docker-compose logs -f keycloak
```

### Restart Services
```bash
# Restart specific service
docker-compose restart keycloak

# Restart all services
docker-compose restart
```

### Clean Up
```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v

# Remove all related images
docker-compose down --rmi all
```

## 📋 Common Configurations

### Keycloak Realm Configuration
```json
{
  "realm": "iceberg",
  "enabled": true,
  "accessTokenLifespan": 300,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 36000
}
```

### OpenFGA Model Template
```fga
model
  schema 1.1

type user
  relations
    define can_read_limited: [user:limited_user]

type table
  relations
    define can_read: [user]
    define can_write: [user]

type column
  relations
    define can_read: [user]
    define can_write: [user]
```

### Lakekeeper Catalog Configuration
```json
{
  "catalog": {
    "type": "iceberg",
    "warehouse": "irisa-ot",
    "uri": "http://lakekeeper:8181/catalog",
    "oauth2": {
      "server-uri": "http://keycloak:8080/realms/iceberg/protocol/openid-connect/token",
      "credential": "client_id:client_secret",
      "scope": "lakekeeper"
    }
  }
}
```

## 🚨 Emergency Commands

### Reset OpenFGA Store
```bash
# Delete store
curl -X DELETE http://openfga:8080/stores/$STORE_ID \
  -H "Authorization: Bearer $TOKEN"

# Create new store
curl -X POST http://openfga:8080/stores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"new-store"}'
```

### Reset Keycloak Realm
```bash
# Export current realm
curl -X GET http://keycloak:8080/admin/realms/iceberg \
  -H "Authorization: Bearer $ADMIN_TOKEN" > realm-backup.json

# Delete realm
curl -X DELETE http://keycloak:8080/admin/realms/iceberg \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Import realm
curl -X POST http://keycloak:8080/admin/realms \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d @realm-backup.json
```

### Emergency Access
```bash
# Get admin token
curl -X POST http://keycloak:8080/realms/master/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin"
```

## 📚 Useful URLs

- **Keycloak Admin Console**: `http://localhost:30080`
- **Lakekeeper API**: `http://localhost:8181`
- **Jupyter Notebooks**: `http://localhost:8889`
- **MinIO Console**: `http://localhost:9001`
- **Trino**: `http://localhost:9999` (when using trino profile)
- **StarRocks**: `http://localhost:8030` (when using starrocks profile)

### OpenFGA Access
OpenFGA playground is disabled due to OIDC authentication requirements. To access OpenFGA:

1. **Via API** (programmatic access):
   ```bash
   curl http://openfga:8080/healthz
   ```

2. **Via Docker exec** (for debugging):
   ```bash
   docker exec -it openfga /bin/sh
   ```

3. **Alternative**: Use the deployment scripts provided in the `openfga/` directory

## 🔍 Debug Tools

### JQ Commands
```bash
# Extract token from response
curl ... | jq -r '.access_token'

# Decode JWT payload
echo $TOKEN | jq -R 'split(".") | .[1] | @base64d | fromjson'

# Pretty print JSON
echo $JSON | jq '.'
```

### Curl Debug
```bash
# Verbose output
curl -v -X POST ...

# Show response headers
curl -i -X POST ...

# Follow redirects
curl -L -X POST ...
```

This quick reference guide covers the most common operations for managing fine-grained access control. For detailed explanations, refer to the main tutorial documentation. 