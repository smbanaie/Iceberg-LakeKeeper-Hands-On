# Keycloak Realm Configuration Guide

This document provides a comprehensive guide to the `realm.json` file, which configures the Keycloak identity provider for the Lakekeeper access control system.

## 🎯 **Overview**

The `realm.json` file defines the complete configuration for the `iceberg` realm in Keycloak, including users, clients, roles, and security settings. This realm serves as the central identity provider for the entire data lake platform.

## 📁 **File Location**
```
ingestion-pipeline/docker/keycloak/realm.json
```

## 🏗️ **Realm Structure Overview**

### **Core Components**
1. **Realm Settings** - Basic configuration and security policies
2. **Users** - Human users and service accounts
3. **Clients** - Applications that can authenticate
4. **Roles** - Permission definitions and hierarchies
5. **Client Scopes** - Token content and permission scopes
6. **Components** - Security providers and policies

## 🔧 **Step-by-Step Configuration Guide**

### **Step 1: Understanding Realm Basics**

#### **1.1 Realm Information**
```json
{
  "realm": "iceberg",
  "displayName": "",
  "enabled": true,
  "sslRequired": "external"
}
```

**What This Means:**
- **Realm Name**: `iceberg` - The unique identifier for this realm
- **Enabled**: `true` - The realm is active and accepting requests
- **SSL Required**: `external` - HTTPS required for external connections

#### **1.2 Security Settings**
```json
{
  "accessTokenLifespan": 300,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 36000,
  "defaultSignatureAlgorithm": "RS256"
}
```

**Configuration Details:**
- **Access Token Lifespan**: 300 seconds (5 minutes) - How long tokens are valid
- **SSO Session Idle Timeout**: 1800 seconds (30 minutes) - Session timeout
- **SSO Session Max Lifespan**: 36000 seconds (10 hours) - Maximum session duration
- **Signature Algorithm**: RS256 - RSA with SHA-256 for token signing

### **Step 2: User Management**

#### **2.1 Human Users**
```json
{
  "users": [
    {
      "id": "cfb55bf6-fcbb-4a1e-bfec-30c6649b52f8",
      "username": "peter",
      "firstName": "Peter",
      "lastName": "Cold",
      "email": "peter@example.com",
      "emailVerified": true,
      "enabled": true,
      "credentials": [
        {
          "type": "password",
          "secretData": "{\"value\":\"BuViHNDGmCq80fvpty/QoggTI8NSt0CuNDGgeoa5f5A=\",\"salt\":\"RJ0aLMQ2qKbZuROs7qQhcA==\",\"additionalParameters\":{}}",
          "credentialData": "{\"hashIterations\":5,\"algorithm\":\"argon2\",\"additionalParameters\":{\"hashLength\":[\"32\"],\"memory\":[\"7168\"],\"type\":[\"id\"],\"version\":[\"1.3\"],\"parallelism\":[\"1\"]}}"
        }
      ],
      "realmRoles": ["default-roles-iceberg"]
    }
  ]
}
```

**How to Add a New Human User:**

1. **Generate User ID**:
   ```bash
   # Generate a UUID for the user
   uuidgen
   ```

2. **Hash the Password**:
   ```bash
   # Use Keycloak's password hashing (argon2)
   # The password "iceberg" becomes the hashed value in secretData
   ```

3. **Create User Entry**:
   ```json
   {
     "id": "NEW-UUID-HERE",
     "username": "newuser",
     "firstName": "New",
     "lastName": "User", 
     "email": "newuser@example.com",
     "emailVerified": true,
     "enabled": true,
     "credentials": [
       {
         "type": "password",
         "secretData": "HASHED_PASSWORD_HERE",
         "credentialData": "{\"hashIterations\":5,\"algorithm\":\"argon2\",\"additionalParameters\":{\"hashLength\":[\"32\"],\"memory\":[\"7168\"],\"type\":[\"id\"],\"version\":[\"1.3\"],\"parallelism\":[\"1\"]}}"
       }
     ],
     "realmRoles": ["default-roles-iceberg"]
   }
   ```

#### **2.2 Service Accounts**
```json
{
  "id": "9410d0bf-4487-4177-a34f-af364cac0a59",
  "username": "service-account-spark",
  "emailVerified": false,
  "enabled": true,
  "serviceAccountClientId": "spark",
  "realmRoles": ["default-roles-iceberg"]
}
```

**How to Add a New Service Account:**

1. **Create Service Account User**:
   ```json
   {
     "id": "NEW-SERVICE-UUID",
     "username": "service-account-NEWSERVICE",
     "emailVerified": false,
     "enabled": true,
     "serviceAccountClientId": "NEWSERVICE",
     "realmRoles": ["default-roles-iceberg"]
   }
   ```

2. **Create Corresponding Client** (see Step 3)

### **Step 3: Client Configuration**

#### **3.1 Service Account Client**
```json
{
  "id": "258e7e0e-db60-4abd-a1ff-ebb475ecd057",
  "clientId": "spark",
  "name": "Spark",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "2OR3eRvYfSZzzZ16MlPd95jhLnOaLM52",
  "serviceAccountsEnabled": true,
  "standardFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "publicClient": false,
  "protocol": "openid-connect",
  "attributes": {
    "access.token.lifespan": "3600",
    "client.secret.creation.time": "1733666693"
  }
}
```

**How to Add a New Service Client:**

1. **Generate Client Secret**:
   ```bash
   # Generate a random secret (32 characters recommended)
   openssl rand -base64 24
   ```

2. **Create Client Entry**:
   ```json
   {
     "id": "NEW-CLIENT-UUID",
     "clientId": "NEWSERVICE",
     "name": "New Service",
     "enabled": true,
     "clientAuthenticatorType": "client-secret",
     "secret": "GENERATED_SECRET_HERE",
     "serviceAccountsEnabled": true,
     "standardFlowEnabled": false,
     "directAccessGrantsEnabled": false,
     "publicClient": false,
     "protocol": "openid-connect",
     "attributes": {
       "access.token.lifespan": "3600",
       "client.secret.creation.time": "TIMESTAMP"
     }
   }
   ```

#### **3.2 Public Client (UI)**
```json
{
  "id": "fe1573cc-fafb-4a37-b621-0133ad3e65f2",
  "clientId": "lakekeeper",
  "name": "Lakekeeper Catalog",
  "enabled": true,
  "publicClient": true,
  "standardFlowEnabled": true,
  "redirectUris": ["*"],
  "webOrigins": ["*"],
  "protocol": "openid-connect"
}
```

**How to Add a New Public Client:**

```json
{
  "id": "NEW-PUBLIC-CLIENT-UUID",
  "clientId": "NEWAPP",
  "name": "New Application",
  "enabled": true,
  "publicClient": true,
  "standardFlowEnabled": true,
  "redirectUris": ["http://localhost:3000/*"],
  "webOrigins": ["http://localhost:3000"],
  "protocol": "openid-connect"
}
```

### **Step 4: Role Configuration**

#### **4.1 Realm Roles**
```json
{
  "roles": {
    "realm": [
      {
        "id": "95e2e174-4bed-4dbb-86b5-6d403bec2eab",
        "name": "default-roles-iceberg",
        "description": "${role_default-roles}",
        "composite": true,
        "composites": {
          "realm": ["offline_access", "uma_authorization"],
          "client": {
            "account": ["view-profile", "manage-account"]
          }
        }
      }
    ]
  }
}
```

**How to Add a New Realm Role:**

```json
{
  "id": "NEW-ROLE-UUID",
  "name": "data-scientist",
  "description": "Data Scientist Role",
  "composite": false,
  "clientRole": false,
  "containerId": "3cbd4538-206e-4310-8846-ae9d9ba63d28"
}
```

#### **4.2 Client Roles**
```json
{
  "client": {
    "lakekeeper": [
      {
        "id": "NEW-CLIENT-ROLE-UUID",
        "name": "lakekeeper-admin",
        "description": "Lakekeeper Administrator",
        "composite": false,
        "clientRole": true,
        "containerId": "CLIENT-ID"
      }
    ]
  }
}
```

### **Step 5: Client Scopes**

#### **5.1 Custom Scopes**
```json
{
  "clientScopes": [
    {
      "id": "ffd7b76d-d12a-4613-aea5-7333b4c9aede",
      "name": "lakekeeper",
      "description": "Client of Lakekeeper",
      "protocol": "openid-connect",
      "attributes": {
        "include.in.token.scope": "false",
        "display.on.consent.screen": "true"
      },
      "protocolMappers": [
        {
          "id": "b7c23ad5-e872-42f9-bc6f-3b0e84ef50ec",
          "name": "Add lakekeeper Audience",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-audience-mapper",
          "config": {
            "included.client.audience": "lakekeeper",
            "access.token.claim": "true"
          }
        }
      ]
    }
  ]
}
```

**How to Add a New Client Scope:**

```json
{
  "id": "NEW-SCOPE-UUID",
  "name": "newscope",
  "description": "New Application Scope",
  "protocol": "openid-connect",
  "attributes": {
    "include.in.token.scope": "false",
    "display.on.consent.screen": "true"
  },
  "protocolMappers": [
    {
      "id": "NEW-MAPPER-UUID",
      "name": "Add newscope Audience",
      "protocol": "openid-connect",
      "protocolMapper": "oidc-audience-mapper",
      "config": {
        "included.client.audience": "newscope",
        "access.token.claim": "true"
      }
    }
  ]
}
```

## 🔐 **Security Best Practices**

### **1. Password Security**
- Use **Argon2** hashing algorithm (already configured)
- Set appropriate **hash iterations** (currently 5)
- Use **strong passwords** for service accounts

### **2. Token Security**
- **Short token lifespans** (300 seconds for access tokens)
- **Secure client secrets** (32+ characters)
- **HTTPS enforcement** for external connections

### **3. Client Configuration**
- **Service accounts**: Use client secrets
- **Public clients**: No secrets, use PKCE
- **Redirect URIs**: Restrict to specific domains
- **Web Origins**: Limit CORS origins

## 🛠️ **Working with the Realm**

### **Method 1: Direct File Editing**

1. **Backup the current realm**:
   ```bash
   cp realm.json realm.json.backup
   ```

2. **Make your changes** to the JSON file

3. **Validate JSON syntax**:
   ```bash
   python -m json.tool realm.json
   ```

4. **Restart Keycloak** to apply changes:
   ```bash
   docker compose restart keycloak
   ```

### **Method 2: Using Keycloak Admin Console**

1. **Access the admin console**: http://localhost:30080
2. **Login as admin**: admin/admin
3. **Select the iceberg realm**
4. **Make changes through the UI**
5. **Export the realm** to get updated JSON

### **Method 3: Using Keycloak CLI**

1. **Login to Keycloak CLI**:
   ```bash
   docker exec -it keycloak /opt/keycloak/bin/kc.sh config credentials \
     --server http://localhost:8080 \
     --realm master \
     --user admin \
     --password admin
   ```

2. **Export realm**:
   ```bash
   docker exec -it keycloak /opt/keycloak/bin/kc.sh get realms/iceberg \
     --output-format=json > realm-export.json
   ```

3. **Import realm**:
   ```bash
   docker exec -it keycloak /opt/keycloak/bin/kc.sh create realms \
     --file realm-export.json
   ```

## 🔍 **Common Operations**

### **Adding a New User**

1. **Generate UUID** for the user
2. **Hash the password** using Argon2
3. **Add user entry** to the users array
4. **Assign appropriate roles**

### **Adding a New Service Account**

1. **Create service account user** (no password)
2. **Create corresponding client** with secret
3. **Enable service accounts** on the client
4. **Assign appropriate roles**

### **Adding a New Client**

1. **Generate client secret**
2. **Create client entry** with appropriate settings
3. **Configure redirect URIs** and web origins
4. **Assign client scopes**

### **Adding a New Role**

1. **Create role entry** in roles section
2. **Assign to users** as needed
3. **Configure role hierarchy** if composite

## ⚠️ **Important Notes**

### **UUID Generation**
- All IDs must be valid UUIDs
- Use tools like `uuidgen` or online UUID generators
- Ensure uniqueness across the realm

### **Password Hashing**
- Keycloak uses Argon2 for password hashing
- The `secretData` field contains the hashed password
- The `credentialData` field contains hashing parameters

### **Client Secrets**
- Service account clients require secrets
- Public clients (like web apps) don't use secrets
- Secrets should be at least 32 characters long

### **Token Configuration**
- Access tokens: 300 seconds (5 minutes)
- Refresh tokens: Configured per client
- Session timeouts: 30 minutes idle, 10 hours max

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Invalid JSON**: Use `python -m json.tool` to validate
2. **Duplicate UUIDs**: Ensure all IDs are unique
3. **Missing Dependencies**: Check that referenced clients/users exist
4. **Permission Issues**: Verify role assignments

### **Debugging Steps**

1. **Check Keycloak logs**:
   ```bash
   docker compose logs keycloak
   ```

2. **Validate realm import**:
   ```bash
   docker exec -it keycloak /opt/keycloak/bin/kc.sh get realms/iceberg
   ```

3. **Test authentication**:
   ```bash
   curl -X POST http://localhost:30080/realms/iceberg/protocol/openid-connect/token \
     -d "grant_type=client_credentials&client_id=spark&client_secret=SECRET"
   ```

## 📚 **Additional Resources**

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)

---

**The realm.json file is the foundation of the entire access control system. Handle it with care and always maintain backups before making changes.** 