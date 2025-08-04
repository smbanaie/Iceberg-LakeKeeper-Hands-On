# Example: Setting Up User "jane" with Limited Access

This example demonstrates the complete workflow for creating a new user "jane" with access to only 2 columns (ID and Amount) of the `fake_seclink` table.

## Prerequisites

- Docker and Docker Compose installed
- Access to the project files
- Basic understanding of Keycloak and OpenFGA

## Step 1: Start the Services

```bash
# Navigate to the project directory
cd ingestion-pipeline/docker

# Start all services
docker-compose -f compose-lakekeeper-pyiceberg-access-control.yaml up -d

# Wait for services to be ready
sleep 30
```

## Step 2: Create User via Keycloak UI

### 2.1 Access Keycloak Admin Console

1. Open browser: `http://localhost:30080`
2. Login with: `admin/admin`
3. Click on "iceberg" realm

### 2.2 Create User "jane"

1. **Go to Users**:
   - Click "Users" in the left sidebar
   - Click "Add user"

2. **Fill User Details**:
   - Username: `jane`
   - Email: `jane@example.com`
   - First Name: `Jane`
   - Last Name: `Analyst`
   - Email Verified: `ON`
   - Click "Save"

3. **Set Password**:
   - Go to "Credentials" tab
   - Password: `password123`
   - Temporary: `OFF`
   - Click "Set Password"

4. **Assign Roles**:
   - Go to "Role Mappings" tab
   - Add "default-roles-iceberg" to "Assigned roles"

### 2.3 Create Client for User

1. **Go to Clients**:
   - Click "Clients" in the left sidebar
   - Click "Create"

2. **Configure Client**:
   - Client ID: `jane-client`
   - Name: `Jane Limited Access Client`
   - Click "Save"

3. **Client Settings**:
   - **Settings tab**:
     - Access Type: `confidential`
     - Service Accounts Enabled: `ON`
     - Valid Redirect URIs: `*`
   - **Credentials tab**:
     - Copy the generated secret (e.g., `JaneSecretKey123456789`)
   - **Client Scopes tab**:
     - Add `jane-limited` to "Assigned optional client scopes"

## Step 3: Create OpenFGA Authorization Model

### 3.1 Create the Model File

Create `jane-limited-access-model.fga`:

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

### 3.2 Create the Tuples File

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

## Step 4: Deploy the Authorization Model

### 4.1 Create Deployment Script

Create `deploy-jane-limited-access.sh`:

```bash
#!/bin/bash

echo "🚀 Deploying OpenFGA authorization model for Jane limited access..."

# Wait for OpenFGA to be ready
echo "⏳ Waiting for OpenFGA to be ready..."
until curl -s http://openfga:8080/healthz > /dev/null; do
    sleep 2
done

# Get store ID (create if doesn't exist)
echo "📝 Getting or creating store..."
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

### 4.2 Run the Deployment

```bash
# Make script executable
chmod +x deploy-jane-limited-access.sh

# Run deployment
./deploy-jane-limited-access.sh
```

## Step 5: Test the Access Control

### 5.1 Create Test Notebook

Create `03-05-Jane-Limited-Access-Test.ipynb`:

```python
# Configuration for Jane limited access
CATALOG_URL = "http://lakekeeper:8181/catalog"
KEYCLOAK_TOKEN_ENDPOINT = "http://keycloak:8080/realms/iceberg/protocol/openid-connect/token"
WAREHOUSE = "irisa-ot"

# Jane user credentials (get from Keycloak UI)
CLIENT_ID = "jane-client"
CLIENT_SECRET = "JaneSecretKey123456789"  # Replace with actual secret
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

# Test 3: Compare with full access user
print("\n🔍 Test 3: Comparing with full access user")

# Get token for Trino service account
trino_token_data = {
    'grant_type': 'client_credentials',
    'client_id': 'trino',
    'client_secret': 'AK48QgaKsqdEpP9PomRJw7l2T7qWGHdZ'
}

trino_response = requests.post(KEYCLOAK_TOKEN_ENDPOINT, data=trino_token_data)
if trino_response.status_code == 200:
    trino_token = trino_response.json()['access_token']
    
    trino_headers = {
        'Authorization': f'Bearer {trino_token}',
        'Content-Type': 'application/json'
    }
    
    # Trino should be able to access all columns
    query_data = {
        "sql": "SELECT * FROM irisa.fake_seclink LIMIT 5"
    }
    
    response = requests.post(f"{CATALOG_URL}/query", headers=trino_headers, json=query_data)
    print(f"Trino access status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Trino service account has full access as expected")
    else:
        print(f"❌ Trino access failed: {response.text}")
else:
    print(f"❌ Failed to get Trino token: {trino_response.text}")
```

### 5.2 Run the Tests

1. **Open Jupyter**:
   - Navigate to: `http://localhost:8889`
   - Open `03-05-Jane-Limited-Access-Test.ipynb`

2. **Update the Client Secret**:
   - Replace `JaneSecretKey123456789` with the actual secret from Keycloak UI

3. **Run All Cells**:
   - Execute all cells in the notebook
   - Verify the test results

## Expected Results

### ✅ Successful Tests:
- **Test 1**: Jane can access ID and Amount columns
- **Test 2**: Jane is denied access to Source column
- **Test 3**: Trino service account has full access

### 📊 Access Matrix:
| User | ID | Amount | Source | Destination | DateIn | DateOut | Message |
|------|----|--------|--------|-------------|--------|---------|---------|
| `jane` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `service-account-trino` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Troubleshooting

### Common Issues:

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

### Debug Commands:

```bash
# Check service logs
docker-compose logs keycloak
docker-compose logs openfga
docker-compose logs lakekeeper

# Test OpenFGA API
curl -X POST http://openfga:8080/stores \
  -H "Content-Type: application/json" \
  -d '{"name":"test-store"}'
```

## Summary

This example demonstrates:

1. ✅ **User Creation**: Creating user "jane" via Keycloak UI
2. ✅ **Client Setup**: Configuring client for authentication
3. ✅ **Authorization Model**: Defining column-level permissions
4. ✅ **Access Control**: Enforcing fine-grained permissions
5. ✅ **Testing**: Verifying the access control works correctly

The system now has fine-grained access control where:
- User "jane" can only access ID and Amount columns
- Service accounts maintain full access
- Authorization is enforced at the column level
- Access decisions are made by OpenFGA
- Integration works with Lakekeeper and Apache Iceberg 