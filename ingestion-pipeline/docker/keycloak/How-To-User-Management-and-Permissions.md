# How-To: User Management and Table Permissions

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Adding New Users](#adding-new-users)
- [Setting Table Permissions](#setting-table-permissions)
- [Service Account Management](#service-account-management)
- [Testing Access Control](#testing-access-control)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This guide provides step-by-step instructions for managing users and configuring table permissions in the Iceberg access control system. The process involves:

1. **Keycloak**: Adding users and configuring authentication
2. **OpenFGA**: Setting up authorization rules
3. **Lakekeeper**: Enforcing access control on Iceberg tables

### System Components
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Keycloak  │───▶│   OpenFGA   │───▶│  Lakekeeper │
│ (Users)     │    │ (Rules)     │    │ (Enforce)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Prerequisites

### 1. System Requirements
- Keycloak server running on `http://localhost:8080`
- OpenFGA server running on `http://localhost:8080`
- Lakekeeper configured and running
- Administrative access to all components

### 2. Required Tools
```bash
# Install required tools
curl -sL https://github.com/openfga/cli/releases/latest/download/fga-cli-linux-amd64.tar.gz | tar -xz
sudo mv fga /usr/local/bin/

# Verify installations
keycloak-admin --version
fga version
```

### 3. Environment Variables
```bash
export KEYCLOAK_URL="http://localhost:8080"
export KEYCLOAK_REALM="iceberg-realm"
export KEYCLOAK_ADMIN_USER="admin"
export KEYCLOAK_ADMIN_PASSWORD="admin"
export OPENFGA_URL="http://localhost:8080"
export OPENFGA_STORE_ID="your-store-id"
export OPENFGA_AUTH_MODEL_ID="your-model-id"
```

## Adding New Users

### 1. Keycloak User Creation

#### Method A: Using Keycloak Admin CLI
```bash
# Login to Keycloak
keycloak-admin config credentials \
  --server $KEYCLOAK_URL \
  --realm master \
  --user $KEYCLOAK_ADMIN_USER \
  --password $KEYCLOAK_ADMIN_PASSWORD

# Create new user
keycloak-admin create users \
  --realm $KEYCLOAK_REALM \
  --username "john" \
  --email "john@example.com" \
  --firstName "John" \
  --lastName "Smith" \
  --enabled true \
  --emailVerified true

# Set password
keycloak-admin set-password \
  --realm $KEYCLOAK_REALM \
  --username "john" \
  --new-password "securepassword123"

# Assign role
keycloak-admin add-roles \
  --realm $KEYCLOAK_REALM \
  --uusername "john" \
  --rolename "iceberg-user"
```

#### Method B: Using REST API
```bash
# Get admin token
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/auth/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=admin-cli&username=$KEYCLOAK_ADMIN_USER&password=$KEYCLOAK_ADMIN_PASSWORD" \
  | jq -r '.access_token')

# Create user
curl -X POST "$KEYCLOAK_URL/auth/admin/realms/$KEYCLOAK_REALM/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "enabled": true,
    "emailVerified": true,
    "firstName": "John",
    "lastName": "Smith",
    "email": "john@example.com",
    "credentials": [
      {
        "type": "password",
        "value": "securepassword123",
        "temporary": false
      }
    ],
    "realmRoles": ["iceberg-user"],
    "attributes": {
      "department": ["engineering"],
      "access_level": ["limited"]
    }
  }'
```

#### Method C: Using Realm Configuration
Add the user to `realm.json` and import:

```json
{
  "username": "john",
  "enabled": true,
  "emailVerified": true,
  "firstName": "John",
  "lastName": "Smith",
  "email": "john@example.com",
  "credentials": [
    {
      "type": "password",
      "value": "securepassword123",
      "temporary": false
    }
  ],
  "realmRoles": ["iceberg-user"],
  "attributes": {
    "department": ["engineering"],
    "access_level": ["limited"]
  }
}
```

### 2. Verify User Creation
```bash
# Check user exists
keycloak-admin get users \
  --realm $KEYCLOAK_REALM \
  --username "john"

# Test authentication
curl -X POST "$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=lakekeeper-client&username=john&password=securepassword123"
```

## Setting Table Permissions

### 1. Understanding Permission Levels

#### Access Control Matrix
| Permission Level | Description | Example Users |
|------------------|-------------|---------------|
| **Full Access** | Read/write all columns | service accounts |
| **Limited Access** | Read specific columns only | regular users |
| **Restricted Access** | No access to sensitive data | external users |

#### Column Access Levels
```json
{
  "limited_columns": ["id_column", "amount_column"],
  "restricted_columns": ["source_column", "destination_column", "datein_column", "dateout_column", "message_column"]
}
```

### 2. OpenFGA Authorization Model

#### Step 1: Create Authorization Model
```bash
# Create new authorization model
fga model write \
  --store-id $OPENFGA_STORE_ID \
  --file authorization-model.json
```

**authorization-model.json:**
```json
{
  "schema_version": "1.1",
  "type_definitions": [
    {
      "type": "user",
      "relations": {
        "can_read_limited_columns": {
          "union": {
            "child": [{ "this": {} }]
          }
        }
      },
      "metadata": {
        "relations": {
          "can_read_limited_columns": {
            "directly_related_user_types": [
              { "type": "user", "id": "john" }
            ]
          }
        }
      }
    },
    {
      "type": "fake_seclink_table",
      "relations": {
        "can_read_all": { "this": {} },
        "can_read_limited": { "this": {} },
        "can_write": { "this": {} }
      },
      "metadata": {
        "relations": {
          "can_read_all": {
            "directly_related_user_types": [
              { "type": "user", "id": "service-account-trino" },
              { "type": "user", "id": "service-account-starrocks" },
              { "type": "user", "id": "service-account-duckdb" }
            ]
          },
          "can_read_limited": {
            "directly_related_user_types": [{ "type": "user", "id": "john" }]
          }
        }
      }
    },
    {
      "type": "id_column",
      "relations": {
        "can_read": { "this": {} }
      },
      "metadata": {
        "relations": {
          "can_read": {
            "directly_related_user_types": [
              { "type": "user", "id": "john" },
              { "type": "user", "id": "service-account-trino" },
              { "type": "user", "id": "service-account-starrocks" },
              { "type": "user", "id": "service-account-duckdb" }
            ]
          }
        }
      }
    },
    {
      "type": "amount_column",
      "relations": {
        "can_read": { "this": {} }
      },
      "metadata": {
        "relations": {
          "can_read": {
            "directly_related_user_types": [
              { "type": "user", "id": "john" },
              { "type": "user", "id": "service-account-trino" },
              { "type": "user", "id": "service-account-starrocks" },
              { "type": "user", "id": "service-account-duckdb" }
            ]
          }
        }
      }
    }
  ]
}
```

#### Step 2: Create Authorization Tuples
```bash
# Create authorization tuples
fga tuple write \
  --store-id $OPENFGA_STORE_ID \
  --file authorization-tuples.json
```

**authorization-tuples.json:**
```json
{
  "tuple_keys": [
    {
      "user": "user:john",
      "relation": "can_read_limited_columns",
      "object": "user:john"
    },
    {
      "user": "user:john",
      "relation": "can_read_limited",
      "object": "fake_seclink_table:table"
    },
    {
      "user": "user:john",
      "relation": "can_read",
      "object": "id_column:column"
    },
    {
      "user": "user:john",
      "relation": "can_read",
      "object": "amount_column:column"
    }
  ]
}
```

### 3. Column-Level Security Configuration

#### Limited Access Columns
```json
{
  "columns": ["id_column", "amount_column"],
  "users": ["john"],
  "permissions": ["read"]
}
```

#### Restricted Access Columns
```json
{
  "columns": ["source_column", "destination_column", "datein_column", "dateout_column", "message_column"],
  "users": ["service-account-trino", "service-account-starrocks", "service-account-duckdb"],
  "permissions": ["read"]
}
```

### 4. Row-Level Security (Optional)

#### Time-Based Access
```json
{
  "condition": "current_time < expiration_time",
  "users": ["john"],
  "tables": ["fake_seclink_table"],
  "expiration": "2024-12-31T23:59:59Z"
}
```

#### Department-Based Access
```json
{
  "condition": "user.department == row.department",
  "users": ["john"],
  "tables": ["fake_seclink_table"],
  "attribute": "department"
}
```

## Service Account Management

### 1. Creating Service Accounts

#### Method A: Using Keycloak Admin CLI
```bash
# Create service account user
keycloak-admin create users \
  --realm $KEYCLOAK_REALM \
  --username "service-account-analytics" \
  --enabled true

# Assign service account role
keycloak-admin add-roles \
  --realm $KEYCLOAK_REALM \
  --uusername "service-account-analytics" \
  --rolename "service-account"

# Set attributes
keycloak-admin update users \
  --realm $KEYCLOAK_REALM \
  --username "service-account-analytics" \
  --attributes '{"client_type":["analytics"],"access_level":["full"]}'
```

#### Method B: Using REST API
```bash
# Create service account
curl -X POST "$KEYCLOAK_URL/auth/admin/realms/$KEYCLOAK_REALM/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "service-account-analytics",
    "enabled": true,
    "realmRoles": ["service-account"],
    "attributes": {
      "client_type": ["analytics"],
      "access_level": ["full"]
    }
  }'
```

### 2. Service Account Permissions
```json
{
  "service_accounts": {
    "service-account-trino": {
      "tables": ["fake_seclink_table"],
      "permissions": ["read_all", "write"],
      "columns": ["*"]
    },
    "service-account-starrocks": {
      "tables": ["fake_seclink_table"],
      "permissions": ["read_all", "write"],
      "columns": ["*"]
    },
    "service-account-duckdb": {
      "tables": ["fake_seclink_table"],
      "permissions": ["read_all", "write"],
      "columns": ["*"]
    }
  }
}
```

## Testing Access Control

### 1. Authentication Testing
```bash
# Test user login
curl -X POST "$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=lakekeeper-client&username=john&password=securepassword123"

# Extract access token
JWT_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=lakekeeper-client&username=john&password=securepassword123" \
  | jq -r '.access_token')

# Decode token to verify claims
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d | jq
```

### 2. Authorization Testing
```bash
# Test OpenFGA authorization
fga check \
  --store-id $OPENFGA_STORE_ID \
  --user "user:john" \
  --relation "can_read" \
  --object "id_column:column"

# Expected result: {"allowed": true}
```

### 3. Lakekeeper Integration Testing
```bash
# Test table access with JWT token
curl -X GET "http://localhost:8080/api/tables/fake_seclink_table" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"

# Test column access
curl -X GET "http://localhost:8080/api/tables/fake_seclink_table/columns" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### 4. Using Jupyter Notebooks
```python
# Test access in Jupyter notebook
import requests
import json

# Get token
token_response = requests.post(
    "http://localhost:8080/auth/realms/iceberg-realm/protocol/openid-connect/token",
    data={
        "grant_type": "password",
        "client_id": "lakekeeper-client",
        "username": "john",
        "password": "securepassword123"
    }
)
token = token_response.json()["access_token"]

# Test table access
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8080/api/tables/fake_seclink_table",
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Data: {response.json()}")
```

## Common Operations

### 1. User Management Commands

#### List All Users
```bash
keycloak-admin get users --realm $KEYCLOAK_REALM
```

#### Update User Attributes
```bash
keycloak-admin update users \
  --realm $KEYCLOAK_REALM \
  --username "john" \
  --attributes '{"access_level":["full"],"department":["analytics"]}'
```

#### Disable User
```bash
keycloak-admin update users \
  --realm $KEYCLOAK_REALM \
  --username "john" \
  --enabled false
```

#### Delete User
```bash
keycloak-admin delete users \
  --realm $KEYCLOAK_REALM \
  --username "john"
```

### 2. Permission Management Commands

#### List Authorization Tuples
```bash
fga tuple read \
  --store-id $OPENFGA_STORE_ID \
  --user "user:john"
```

#### Add Permission
```bash
fga tuple write \
  --store-id $OPENFGA_STORE_ID \
  --user "user:john" \
  --relation "can_read" \
  --object "new_column:column"
```

#### Remove Permission
```bash
fga tuple delete \
  --store-id $OPENFGA_STORE_ID \
  --user "user:john" \
  --relation "can_read" \
  --object "restricted_column:column"
```

### 3. Bulk Operations

#### Import Multiple Users
```bash
# Create users from JSON file
cat users.json | jq -c '.users[]' | while read user; do
  curl -X POST "$KEYCLOAK_URL/auth/admin/realms/$KEYCLOAK_REALM/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$user"
done
```

#### Import Multiple Permissions
```bash
# Import permissions from JSON file
fga tuple write \
  --store-id $OPENFGA_STORE_ID \
  --file permissions.json
```

## Troubleshooting

### 1. Common Issues

#### Authentication Failures
**Problem**: User cannot authenticate
```bash
# Check user exists and is enabled
keycloak-admin get users \
  --realm $KEYCLOAK_REALM \
  --username "john"

# Check user credentials
keycloak-admin get users \
  --realm $KEYCLOAK_REALM \
  --username "john" \
  --fields "credentials"
```

**Solution**: Verify user configuration and credentials

#### Authorization Failures
**Problem**: User cannot access resources
```bash
# Check OpenFGA authorization
fga check \
  --store-id $OPENFGA_STORE_ID \
  --user "user:john" \
  --relation "can_read" \
  --object "id_column:column"

# List user permissions
fga tuple read \
  --store-id $OPENFGA_STORE_ID \
  --user "user:john"
```

**Solution**: Verify authorization tuples and model

#### Token Issues
**Problem**: Invalid or expired tokens
```bash
# Decode and verify token
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d | jq

# Check token expiration
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d | jq '.exp'
```

**Solution**: Refresh token or check token configuration

### 2. Debugging Steps

#### Step 1: Verify Keycloak Configuration
```bash
# Check realm configuration
keycloak-admin get realms --realm $KEYCLOAK_REALM

# Check client configuration
keycloak-admin get clients \
  --realm $KEYCLOAK_REALM \
  --clientid "lakekeeper-client"
```

#### Step 2: Verify OpenFGA Configuration
```bash
# Check authorization model
fga model read \
  --store-id $OPENFGA_STORE_ID

# Check authorization tuples
fga tuple read \
  --store-id $OPENFGA_STORE_ID
```

#### Step 3: Test Integration
```bash
# Test complete flow
./test-integration.sh john securepassword123
```

### 3. Log Analysis

#### Keycloak Logs
```bash
# Check Keycloak server logs
docker logs keycloak-server | grep -i "john"

# Check authentication attempts
docker logs keycloak-server | grep -i "login"
```

#### OpenFGA Logs
```bash
# Check OpenFGA server logs
docker logs openfga-server | grep -i "authorization"

# Check authorization requests
docker logs openfga-server | grep -i "check"
```

#### Lakekeeper Logs
```bash
# Check Lakekeeper logs
docker logs lakekeeper-server | grep -i "access"

# Check table access attempts
docker logs lakekeeper-server | grep -i "fake_seclink_table"
```

## Best Practices

### 1. Security Best Practices

#### Password Policies
- Enforce strong password requirements
- Implement password expiration
- Use secure password storage

#### Token Management
- Set appropriate token expiration times
- Implement token refresh mechanisms
- Use secure token storage

#### Access Control
- Follow principle of least privilege
- Regular access reviews
- Monitor access patterns

### 2. Operational Best Practices

#### User Management
- Use consistent naming conventions
- Document user roles and permissions
- Regular user account audits

#### Configuration Management
- Version control all configurations
- Use environment-specific settings
- Document configuration changes

#### Monitoring and Alerting
- Monitor authentication failures
- Track authorization decisions
- Alert on suspicious activities

### 3. Performance Best Practices

#### Caching
- Cache user information
- Cache authorization decisions
- Use appropriate cache TTL

#### Connection Management
- Use connection pooling
- Implement retry mechanisms
- Monitor connection usage

#### Resource Optimization
- Optimize database queries
- Use efficient data structures
- Monitor resource usage

## Related Documentation

- [Keycloak Concepts and Realm Configuration](Keycloak-Concepts-and-Realm-Explanation.md) - Keycloak concepts and realm.json explanation
- [Keycloak-OpenFGA Integration](Keycloak-OpenFGA-Integration.md) - Integration guide 