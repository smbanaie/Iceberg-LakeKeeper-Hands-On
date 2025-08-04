# Fine-Grained Access Control Tutorial for Keycloak

This tutorial provides a comprehensive guide to implementing fine-grained access control (FGAC) for Apache Iceberg tables using Keycloak, OpenFGA, and Lakekeeper.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Step 1: Understanding the Components](#step-1-understanding-the-components)
5. [Step 2: Adding Users via JSON Configuration](#step-2-adding-users-via-json-configuration)
6. [Step 3: Adding Users via Keycloak UI](#step-3-adding-users-via-keycloak-ui)
7. [Step 4: Creating OpenFGA Authorization Model](#step-4-creating-openfga-authorization-model)
8. [Step 5: Setting Up Column-Level Permissions](#step-5-setting-up-column-level-permissions)
9. [Step 6: Testing the Access Control](#step-6-testing-the-access-control)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

## Overview

Fine-grained access control allows you to restrict user access to specific columns or rows in your data tables. This tutorial demonstrates how to:

- Create users with different access levels
- Implement column-level security
- Use OpenFGA for authorization decisions
- Integrate with Lakekeeper for Iceberg catalog management

## Architecture

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

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of Keycloak, OpenFGA, and Apache Iceberg
- Access to the project files

## Step 1: Understanding the Components

### Keycloak (Authentication)
- **Purpose**: User authentication and identity management
- **Role**: Issues JWT tokens with user claims
- **Integration**: Works with OpenFGA for authorization

### OpenFGA (Authorization)
- **Purpose**: Fine-grained authorization decisions
- **Role**: Determines what columns/tables users can access
- **Model**: Defines relationships between users, objects, and permissions

### Lakekeeper (Catalog Management)
- **Purpose**: Apache Iceberg catalog management
- **Role**: Enforces OpenFGA decisions on table access
- **Integration**: Consults OpenFGA for authorization

## Step 2: Adding Users via JSON Configuration

### 2.1 Understanding the User Structure

Users in Keycloak are defined in the `realm.json` file. Here's the structure:

```json
{
  "id": "unique-user-id",
  "username": "username",
  "firstName": "First",
  "lastName": "Last",
  "email": "user@example.com",
  "emailVerified": true,
  "enabled": true,
  "credentials": [
    {
      "type": "password",
      "value": "hashed-password",
      "temporary": false
    }
  ],
  "realmRoles": ["default-roles-iceberg"],
  "groups": []
}
```

### 2.2 Adding a New User

#### Example: Adding User "john" with Limited Access

```json
{
  "id": "john-user-id-1234-5678-9abc-def0",
  "username": "john",
  "firstName": "John",
  "lastName": "Limited",
  "email": "john@example.com",
  "emailVerified": true,
  "createdTimestamp": 1735995480968,
  "enabled": true,
  "totp": false,
  "credentials": [
    {
      "id": "john-credential-id-1234-5678-9abc-def0",
      "type": "password",
      "userLabel": "John's password",
      "createdDate": 1735995502485,
      "secretData": "{\"value\":\"hashed-password-here\",\"salt\":\"salt-value\",\"additionalParameters\":{}}",
      "credentialData": "{\"hashIterations\":5,\"algorithm\":\"argon2\",\"additionalParameters\":{\"hashLength\":[\"32\"],\"memory\":[\"7168\"],\"type\":[\"id\"],\"version\":[\"1.3\"],\"parallelism\":[\"1\"]}}"
    }
  ],
  "disableableCredentialTypes": [],
  "requiredActions": [],
  "realmRoles": ["default-roles-iceberg"],
  "notBefore": 0,
  "groups": []
}
```

#### Steps to Add User via JSON:

1. **Generate a unique ID**:
   ```bash
   # Use UUID or timestamp-based ID
   echo "user-$(date +%s)-$(openssl rand -hex 8)"
   ```

2. **Hash the password**:
   ```bash
   # Use Keycloak's password hashing
   # For development, you can use a simple hash
   echo -n "password123" | openssl dgst -sha256
   ```

3. **Add to realm.json**:
   - Open `realm.json`
   - Find the `users` array
   - Add the new user object
   - Ensure proper JSON formatting

4. **Restart Keycloak**:
   ```bash
   docker-compose restart keycloak
   ```

### 2.3 Creating a Client for the User

Each user needs a client for authentication:

```json
{
  "id": "john-client-id-1234-5678-9abc-def0",
  "clientId": "john-client",
  "name": "John Limited Access Client",
  "description": "Client for John user with limited column access",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "JohnSecretKey123456789",
  "serviceAccountsEnabled": true,
  "publicClient": false,
  "protocol": "openid-connect",
  "defaultClientScopes": ["web-origins", "acr", "roles", "profile", "basic", "email"],
  "optionalClientScopes": ["lakekeeper", "address", "john-limited", "phone", "offline_access", "sign", "microprofile-jwt"]
}
```

## Step 3: Adding Users via Keycloak UI

### 3.1 Accessing Keycloak Admin Console

1. **Start the services**:
   ```bash
   docker-compose -f compose-lakekeeper-pyiceberg-access-control.yaml up -d
   ```

2. **Access Keycloak**:
   - Open browser: `http://localhost:30080`
   - Login with: `admin/admin`

3. **Navigate to Users**:
   - Click on "iceberg" realm
   - Go to "Users" in the left sidebar

### 3.2 Creating a New User

1. **Click "Add user"**:
   - Fill in the required fields:
     - Username: `jane`
     - Email: `jane@example.com`
     - First Name: `Jane`
     - Last Name: `Analyst`

2. **Set Credentials**:
   - Go to "Credentials" tab
   - Set password: `password123`
   - Uncheck "Temporary password"
   - Click "Set Password"

3. **Assign Roles**:
   - Go to "Role Mappings" tab
   - Add "default-roles-iceberg" to "Assigned roles"

4. **Save the User**:
   - Click "Save" button

### 3.3 Creating a Client for the User

1. **Go to Clients**:
   - Click "Clients" in the left sidebar

2. **Create Client**:
   - Click "Create"
   - Client ID: `jane-client`
   - Name: `Jane Limited Access Client`
   - Click "Save"

3. **Configure Client**:
   - **Settings tab**:
     - Access Type: `confidential`
     - Service Accounts Enabled: `ON`
     - Valid Redirect URIs: `*`
   - **Credentials tab**:
     - Copy the generated secret
   - **Client Scopes tab**:
     - Add `jane-limited` to "Assigned optional client scopes"

## Step 4: Creating OpenFGA Authorization Model

### 4.1 Understanding OpenFGA Model

OpenFGA uses a declarative language to define authorization relationships:

```fga
model
  schema 1.1

type user
  relations
    define can_read_limited_columns: [user:jane]

type table
  relations
    define can_read: [user]
    define can_write: [user]

type column
  relations
    define can_read: [user]
    define can_write: [user]
```

### 4.2 Creating Column-Level Access Model

Create a file `jane-limited-access-model.fga`:

```fga
model
  schema 1.1

type user
  relations
    define can_read_limited_columns: [user:jane]

type table
  relations
    define can_read: [user]
    define can_read_limited_columns: [user]
    define can_write: [user]

type column
  relations
    define can_read: [user]
    define can_write: [user]

# Define the specific table and columns
type fake_seclink_table
  relations
    define can_read_all: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]
    define can_read_limited: [user:jane]
    define can_write: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

# Specific column types for limited access
type id_column
  relations
    define can_read: [user:jane, user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

type amount_column
  relations
    define can_read: [user:jane, user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

type source_column
  relations
    define can_read: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

type destination_column
  relations
    define can_read: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

type datein_column
  relations
    define can_read: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

type dateout_column
  relations
    define can_read: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]

type message_column
  relations
    define can_read: [user:service-account-trino, user:service-account-starrocks, user:service-account-duckdb]
```

## Step 5: Setting Up Column-Level Permissions

### 5.1 Creating Authorization Tuples

Create `jane-limited-access-tuples.json`:

```json
{
  "tuple_keys": [
    {
      "user": "user:jane",
      "relation": "can_read_limited",
      "object": "fake_seclink_table:irisa.fake_seclink"
    },
    {
      "user": "user:jane",
      "relation": "can_read",
      "object": "id_column:irisa.fake_seclink.id"
    },
    {
      "user": "user:jane",
      "relation": "can_read",
      "object": "amount_column:irisa.fake_seclink.amount"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read_all",
      "object": "fake_seclink_table:irisa.fake_seclink"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "id_column:irisa.fake_seclink.id"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "amount_column:irisa.fake_seclink.amount"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "source_column:irisa.fake_seclink.source"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "destination_column:irisa.fake_seclink.destination"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "datein_column:irisa.fake_seclink.datein"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "dateout_column:irisa.fake_seclink.dateout"
    },
    {
      "user": "user:service-account-trino",
      "relation": "can_read",
      "object": "message_column:irisa.fake_seclink.message"
    }
  ]
}
```

### 5.2 Deploying the Authorization Model

Create a deployment script `deploy-jane-limited-access.sh`:

```bash
#!/bin/bash

echo "🚀 Deploying OpenFGA authorization model for Jane limited access..."

# Wait for OpenFGA to be ready
echo "⏳ Waiting for OpenFGA to be ready..."
until curl -s http://openfga:8080/healthz > /dev/null; do
    sleep 2
done

# Get store ID (you'll need to create or get the store ID)
STORE_ID=$(curl -s -X POST http://openfga:8080/stores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(curl -s -X POST http://keycloak:8080/realms/iceberg/protocol/openid-connect/token \
    -d "grant_type=client_credentials" \
    -d "client_id=openfga" \
    -d "client_secret=xqE1vUrifVDKAZdLuz6JAnDxMYLdGu5z" | jq -r '.access_token')" \
  -d '{"name":"iceberg-store"}' | jq -r '.id')

echo "📝 Store ID: $STORE_ID"

# Create the authorization model
echo "📝 Creating authorization model..."
MODEL_ID=$(curl -s -X POST http://openfga:8080/stores/$STORE_ID/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(curl -s -X POST http://keycloak:8080/realms/iceberg/protocol/openid-connect/token \
    -d "grant_type=client_credentials" \
    -d "client_id=openfga" \
    -d "client_secret=xqE1vUrifVDKAZdLuz6JAnDxMYLdGu5z" | jq -r '.access_token')" \
  -d @jane-limited-access-model.fga | jq -r '.authorization_model_id')

echo "📝 Model ID: $MODEL_ID"

# Create the authorization tuples
echo "🔐 Creating authorization tuples..."
curl -X POST http://openfga:8080/stores/$STORE_ID/authorization-models/$MODEL_ID/write \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(curl -s -X POST http://keycloak:8080/realms/iceberg/protocol/openid-connect/token \
    -d "grant_type=client_credentials" \
    -d "client_id=openfga" \
    -d "client_secret=xqE1vUrifVDKAZdLuz6JAnDxMYLdGu5z" | jq -r '.access_token')" \
  -d @jane-limited-access-tuples.json

echo "✅ OpenFGA authorization model deployed successfully!"
echo ""
echo "📋 Summary:"
echo "   - User 'jane' can only access ID and Amount columns"
echo "   - Other service accounts maintain full access"
echo "   - Fine-grained authorization is now active"
```

## Step 6: Testing the Access Control

### 6.1 Creating a Test Notebook

Create `03-05-Jane-Limited-Access-Test.ipynb`:

```python
# Configuration for Jane limited access
CATALOG_URL = "http://lakekeeper:8181/catalog"
KEYCLOAK_TOKEN_ENDPOINT = "http://keycloak:8080/realms/iceberg/protocol/openid-connect/token"
WAREHOUSE = "irisa-ot"

# Jane user credentials
CLIENT_ID = "jane-client"
CLIENT_SECRET = "JaneSecretKey123456789"  # Get this from Keycloak UI
USERNAME = "jane"
PASSWORD = "password123"

import requests
import json

# Get access token for Jane user
def get_jane_token():
    token_url = f"{KEYCLOAK_TOKEN_ENDPOINT}"
    
    # Get token using client credentials
    client_data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=client_data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Error getting client token: {response.text}")
        return None

token = get_jane_token()
print(f"✅ Token obtained: {token[:50]}..." if token else "❌ Failed to get token")

# Test 1: Try to access only ID and Amount columns (should work)
print("🔍 Test 1: Accessing ID and Amount columns (should work)")

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

query_data = {
    "sql": "SELECT ID, Amount FROM irisa.fake_seclink LIMIT 5"
}

response = requests.post(f"{CATALOG_URL}/query", headers=headers, json=query_data)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Success! Jane can access ID and Amount columns")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"❌ Failed: {response.text}")

# Test 2: Try to access Source column (should be denied)
print("\n🔍 Test 2: Accessing Source column (should be denied)")

query_data = {
    "sql": "SELECT ID, Amount, Source FROM irisa.fake_seclink LIMIT 5"
}

response = requests.post(f"{CATALOG_URL}/query", headers=headers, json=query_data)
print(f"Status: {response.status_code}")
if response.status_code == 403:
    print("✅ Success! Access to Source column is properly denied")
    print(f"Error: {response.text}")
else:
    print(f"❌ Unexpected result: {response.text}")
```

### 6.2 Running the Tests

1. **Start the services**:
   ```bash
   docker-compose -f compose-lakekeeper-pyiceberg-access-control.yaml up -d
   ```

2. **Deploy the authorization model**:
   ```bash
   cd ingestion-pipeline/docker/openfga
   chmod +x deploy-jane-limited-access.sh
   ./deploy-jane-limited-access.sh
   ```

3. **Run the test notebook**:
   - Open Jupyter: `http://localhost:8889`
   - Navigate to `03-05-Jane-Limited-Access-Test.ipynb`
   - Run all cells

## Step 7: Advanced Configuration

### 7.1 Row-Level Security

To implement row-level security, extend the OpenFGA model:

```fga
type row
  relations
    define can_read: [user]

type fake_seclink_row
  relations
    define can_read: [user:jane] if user.department = row.department
```

### 7.2 Time-Based Access

Implement time-based access control:

```fga
type time_based_access
  relations
    define can_read: [user] if current_time >= start_time and current_time <= end_time
```

### 7.3 Dynamic Permissions

Use OpenFGA's dynamic permissions:

```fga
type dynamic_permission
  relations
    define can_read: [user] if user.role in ["analyst", "manager"]
```

## Troubleshooting

### Common Issues

1. **Token Expiration**:
   ```bash
   # Check token expiration
   echo $token | jq -R 'split(".") | .[1] | @base64d | fromjson | .exp'
   ```

2. **OpenFGA Connection Issues**:
   ```bash
   # Check OpenFGA health
   curl http://openfga:8080/healthz
   ```

3. **Authorization Denied**:
   ```bash
   # Check OpenFGA tuples
   curl -X POST http://openfga:8080/stores/$STORE_ID/read \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"tuple_key": {"user": "user:jane", "relation": "can_read", "object": "id_column:irisa.fake_seclink.id"}}'
   ```

### Debug Commands

```bash
# Check Keycloak logs
docker-compose logs keycloak

# Check OpenFGA logs
docker-compose logs openfga

# Check Lakekeeper logs
docker-compose logs lakekeeper

# Test OpenFGA API
curl -X POST http://openfga:8080/stores \
  -H "Content-Type: application/json" \
  -d '{"name":"test-store"}'
```

## Best Practices

### 1. Security
- Use strong passwords for all users
- Regularly rotate client secrets
- Implement least privilege principle
- Audit access logs regularly

### 2. Performance
- Cache authorization decisions
- Use efficient OpenFGA queries
- Monitor authorization latency

### 3. Maintenance
- Version control your authorization models
- Document all permission changes
- Regular backup of OpenFGA data
- Test authorization changes in staging

### 4. Monitoring
- Set up alerts for authorization failures
- Monitor token usage and expiration
- Track column access patterns
- Log all authorization decisions

## Conclusion

This tutorial provides a comprehensive guide to implementing fine-grained access control using Keycloak, OpenFGA, and Lakekeeper. The system allows for:

- ✅ User authentication via Keycloak
- ✅ Column-level access control via OpenFGA
- ✅ Integration with Apache Iceberg via Lakekeeper
- ✅ Flexible permission management
- ✅ Scalable authorization architecture

For production deployments, consider:
- High availability setup
- Performance optimization
- Security hardening
- Compliance requirements

## Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenFGA Documentation](https://openfga.dev/docs)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [Lakekeeper Documentation](https://lakekeeper.io/docs) 