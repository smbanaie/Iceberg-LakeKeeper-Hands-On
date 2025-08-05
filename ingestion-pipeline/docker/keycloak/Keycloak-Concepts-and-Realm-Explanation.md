# Keycloak Concepts and Realm Configuration

## Table of Contents
- [Overview](#overview)
- [Keycloak Core Concepts](#keycloak-core-concepts)
- [Realm Configuration Structure](#realm-configuration-structure)
- [Authentication Flow](#authentication-flow)
- [Authorization Integration](#authorization-integration)
- [Configuration Examples](#configuration-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Keycloak is an open-source Identity and Access Management (IAM) solution that provides authentication, authorization, and user management capabilities. In our system, Keycloak handles user authentication and issues JWT tokens that are then used by OpenFGA for fine-grained authorization decisions.

### System Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   Keycloak  │───▶│   OpenFGA   │
│ Application │    │ (Auth)      │    │ (Authz)     │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ Lakekeeper  │
                   │ (Iceberg)   │
                   └─────────────┘
```

## Keycloak Core Concepts

### 1. Realm
A realm is a logical container for users, clients, roles, and security settings. Think of it as a separate tenant or organization.

**Key Characteristics:**
- **Isolation**: Each realm is completely isolated from others
- **Configuration**: Contains its own users, clients, roles, and settings
- **Security**: Independent security policies and authentication flows

**In our system:**
- We use a single realm called "iceberg-realm"
- All users, service accounts, and clients are defined within this realm

### 2. Users
Users represent the individuals or entities that can authenticate with the system.

**User Types in our system:**
- **Regular Users**: Human users like "jane" with limited access
- **Service Accounts**: Non-human users for machine-to-machine authentication
  - `service-account-trino`
  - `service-account-starrocks` 
  - `service-account-duckdb`

**User Properties:**
- **Username**: Unique identifier within the realm
- **Email**: Contact information
- **Attributes**: Custom key-value pairs for additional data
- **Groups**: Organizational units for user management
- **Required Actions**: Actions users must complete (e.g., password change)

### 3. Clients
Clients represent applications or services that interact with Keycloak for authentication.

**Client Types:**
- **Public Clients**: Web applications that can't securely store secrets
- **Confidential Clients**: Server-side applications that can store secrets securely
- **Bearer-Only**: Clients that only accept bearer tokens (no login)

**In our system:**
- **lakekeeper-client**: Confidential client for Lakekeeper integration
- **admin-cli**: Administrative client for realm management

### 4. Roles
Roles define permissions that can be assigned to users or clients.

**Role Types:**
- **Realm Roles**: Available to all users in the realm
- **Client Roles**: Specific to a particular client
- **Composite Roles**: Roles that contain other roles

**In our system:**
- **iceberg-user**: Basic user role with limited permissions
- **iceberg-admin**: Administrative role with full permissions
- **service-account**: Role for service account authentication

### 5. Client Scopes
Client scopes define what information is included in access tokens.

**Standard Scopes:**
- **openid**: Basic OpenID Connect information
- **profile**: User profile information
- **email**: Email address
- **roles**: User roles

**Custom Scopes:**
- **iceberg-access**: Custom scope for Iceberg-specific permissions

## Realm Configuration Structure

The `realm.json` file contains the complete configuration for our Keycloak realm. Here's the structure:

### 1. Realm Metadata
```json
{
  "realm": "iceberg-realm",
  "enabled": true,
  "displayName": "Iceberg Access Control Realm",
  "displayNameHtml": "<div class=\"kc-logo-text\"><span>Iceberg</span></div>"
}
```

### 2. Users Configuration
```json
{
  "users": [
    {
      "username": "jane",
      "enabled": true,
      "emailVerified": true,
      "firstName": "Jane",
      "lastName": "Doe",
      "email": "jane@example.com",
      "credentials": [
        {
          "type": "password",
          "value": "password123",
          "temporary": false
        }
      ],
      "realmRoles": ["iceberg-user"],
      "attributes": {
        "department": ["analytics"],
        "access_level": ["limited"]
      }
    }
  ]
}
```

### 3. Clients Configuration
```json
{
  "clients": [
    {
      "clientId": "lakekeeper-client",
      "enabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "your-secret-here",
      "redirectUris": ["http://localhost:8080/*"],
      "webOrigins": ["http://localhost:8080"],
      "publicClient": false,
      "protocol": "openid-connect",
      "attributes": {
        "saml.assertion.signature": "false",
        "saml.force.post.binding": "false",
        "saml.multivalued.roles": "false",
        "saml.encrypt": "false",
        "saml.server.signature": "false",
        "saml.server.signature.keyinfo.ext": "false",
        "exclude.session.state.from.auth.response": "false",
        "saml_force_name_id_format": "false",
        "saml.client.signature": "false",
        "tls.client.certificate.bound.access.tokens": "false",
        "saml.authnstatement": "false",
        "display.on.consent.screen": "false",
        "saml.onetimeuse.condition": "false"
      }
    }
  ]
}
```

### 4. Roles Configuration
```json
{
  "roles": {
    "realm": [
      {
        "name": "iceberg-user",
        "description": "Basic user with limited access to Iceberg tables",
        "composite": false,
        "clientRole": false,
        "attributes": {}
      },
      {
        "name": "iceberg-admin",
        "description": "Administrative user with full access",
        "composite": false,
        "clientRole": false,
        "attributes": {}
      }
    ]
  }
}
```

### 5. Client Scopes Configuration
```json
{
  "clientScopes": [
    {
      "name": "iceberg-access",
      "description": "Custom scope for Iceberg access control",
      "protocol": "openid-connect",
      "attributes": {
        "include.in.token.scope": "true",
        "display.on.consent.screen": "true"
      },
      "protocolMappers": [
        {
          "name": "iceberg-permissions",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-attribute-mapper",
          "config": {
            "userinfo.token.claim": "true",
            "user.attribute": "iceberg_permissions",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "claim.name": "iceberg_permissions",
            "jsonType.label": "String"
          }
        }
      ]
    }
  ]
}
```

## Authentication Flow

### 1. User Authentication Process
```
1. User submits credentials to Keycloak
2. Keycloak validates credentials against realm configuration
3. Keycloak checks user roles and attributes
4. Keycloak generates JWT token with user claims
5. Client receives JWT token
6. Client includes JWT token in requests to protected resources
```

### 2. JWT Token Structure
```json
{
  "sub": "jane",
  "iss": "http://localhost:8080/auth/realms/iceberg-realm",
  "aud": "lakekeeper-client",
  "exp": 1640995200,
  "iat": 1640908800,
  "realm_access": {
    "roles": ["iceberg-user"]
  },
  "resource_access": {
    "lakekeeper-client": {
      "roles": ["user"]
    }
  },
  "iceberg_permissions": "limited",
  "email": "jane@example.com",
  "preferred_username": "jane"
}
```

### 3. Token Validation
- **Signature**: Verified using realm's public key
- **Expiration**: Checked against current time
- **Audience**: Validated against expected client
- **Issuer**: Confirmed to be from trusted realm

## Authorization Integration

### 1. Keycloak to OpenFGA Flow
```
1. Keycloak authenticates user and issues JWT
2. Client includes JWT in request to Lakekeeper
3. Lakekeeper extracts user information from JWT
4. Lakekeeper queries OpenFGA with user and resource
5. OpenFGA evaluates authorization model
6. OpenFGA returns access decision
7. Lakekeeper enforces access control
```

### 2. User Information Mapping
```json
{
  "user_id": "jane",
  "user_roles": ["iceberg-user"],
  "user_attributes": {
    "department": "analytics",
    "access_level": "limited"
  },
  "permissions": {
    "can_read_limited_columns": true,
    "can_read_restricted_columns": false
  }
}
```

## Configuration Examples

### 1. Adding a New User
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
      "value": "securepassword",
      "temporary": true
    }
  ],
  "realmRoles": ["iceberg-user"],
  "attributes": {
    "department": ["engineering"],
    "access_level": ["limited"]
  }
}
```

### 2. Creating a Service Account
```json
{
  "username": "service-account-analytics",
  "enabled": true,
  "serviceAccountClientId": "analytics-client",
  "realmRoles": ["service-account"],
  "attributes": {
    "client_type": ["analytics"],
    "access_level": ["full"]
  }
}
```

### 3. Defining Custom Attributes
```json
{
  "attributes": {
    "iceberg_permissions": ["read_limited"],
    "department": ["analytics"],
    "access_level": ["limited"],
    "data_sensitivity": ["low"],
    "expiration_date": ["2024-12-31"]
  }
}
```

## Best Practices

### 1. Security Configuration
- **Password Policy**: Enforce strong password requirements
- **Session Timeout**: Set appropriate session durations
- **Token Expiration**: Configure reasonable token lifetimes
- **HTTPS**: Always use HTTPS in production

### 2. User Management
- **Role-Based Access**: Use roles for permission management
- **Attribute-Based Access**: Leverage user attributes for fine-grained control
- **Regular Audits**: Periodically review user access
- **Principle of Least Privilege**: Grant minimum necessary permissions

### 3. Client Configuration
- **Secure Secrets**: Use strong client secrets
- **Redirect URIs**: Restrict to specific domains
- **CORS Configuration**: Configure appropriate origins
- **Token Validation**: Implement proper token validation

### 4. Monitoring and Logging
- **Access Logs**: Monitor authentication attempts
- **Error Tracking**: Log authentication failures
- **Performance Metrics**: Track response times
- **Security Events**: Monitor suspicious activities

## Troubleshooting

### 1. Common Issues

**Authentication Failures:**
- Check user credentials in realm configuration
- Verify user is enabled and not locked
- Confirm user has required roles

**Token Issues:**
- Validate token signature and expiration
- Check client configuration and secrets
- Verify audience and issuer claims

**Authorization Problems:**
- Ensure user has required roles
- Check OpenFGA authorization model
- Verify user attributes match access rules

### 2. Debugging Steps

**1. Check User Configuration:**
```bash
# Verify user exists and is enabled
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8080/auth/admin/realms/iceberg-realm/users?username=jane"
```

**2. Validate Token:**
```bash
# Decode JWT token to check claims
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d | jq
```

**3. Test Authentication:**
```bash
# Test user login
curl -X POST "http://localhost:8080/auth/realms/iceberg-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=lakekeeper-client&username=jane&password=password123"
```

### 3. Configuration Validation

**Realm Configuration:**
- Verify all required users exist
- Check client configurations
- Validate role assignments
- Test authentication flows

**Integration Testing:**
- Test complete authentication flow
- Verify JWT token generation
- Check OpenFGA integration
- Validate access control enforcement

### 4. Performance Optimization

**Token Caching:**
- Implement token caching for performance
- Use appropriate cache TTL
- Monitor cache hit rates

**Connection Pooling:**
- Configure database connection pools
- Optimize LDAP connections
- Monitor connection usage

**Load Balancing:**
- Use multiple Keycloak instances
- Implement proper load balancing
- Monitor instance health

## Related Documentation

- [README.md](README.md) - Main overview and quick start
- [Keycloak-OpenFGA-Integration.md](Keycloak-OpenFGA-Integration.md) - Integration guide
- [How-To: User Management and Table Permissions](How-To-User-Management-and-Permissions.md) - Step-by-step guide for adding users and setting permissions 