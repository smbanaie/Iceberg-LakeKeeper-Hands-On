#!/bin/bash

# Simple deployment script for OpenFGA authorization model
# This can be run from the host system

echo "🚀 Deploying OpenFGA authorization model for Irisa limited access..."

# Check if services are running
echo "⏳ Checking if services are ready..."

# Check OpenFGA
if ! curl -s http://localhost:8080/healthz > /dev/null; then
    echo "❌ OpenFGA is not accessible at http://localhost:8080"
    echo "   Make sure OpenFGA service is running"
    exit 1
fi

# Check Keycloak
if ! curl -s http://localhost:30080/realms/iceberg/.well-known/openid-configuration > /dev/null; then
    echo "❌ Keycloak is not accessible at http://localhost:30080"
    exit 1
fi

echo "✅ Services are ready"

# Get OpenFGA token
echo "🔑 Getting OpenFGA token..."
OPENFGA_TOKEN=$(curl -s -X POST http://localhost:30080/realms/iceberg/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=openfga" \
  -d "client_secret=xqE1vUrifVDKAZdLuz6JAnDxMYLdGu5z" | jq -r '.access_token')

if [ "$OPENFGA_TOKEN" = "null" ] || [ -z "$OPENFGA_TOKEN" ]; then
    echo "❌ Failed to get OpenFGA token"
    exit 1
fi

echo "✅ Token obtained successfully"

# Create or get store
echo "📝 Creating/getting store..."
STORE_RESPONSE=$(curl -s -X POST http://localhost:8080/stores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENFGA_TOKEN" \
  -d '{"name":"iceberg-store"}')

STORE_ID=$(echo "$STORE_RESPONSE" | jq -r '.id')

if [ "$STORE_ID" = "null" ] || [ -z "$STORE_ID" ]; then
    echo "❌ Failed to create/get store"
    echo "Response: $STORE_RESPONSE"
    exit 1
fi

echo "✅ Store ID: $STORE_ID"

# Create the authorization model
MODEL_ID=$(curl -s -X POST http://localhost:8080/stores/$STORE_ID/authorization-models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:30080/realms/iceberg/protocol/openid-connect/token \
    -d "grant_type=client_credentials" \
    -d "client_id=openfga" \
    -d "client_secret=xqE1vUrifVDKAZdLuz6JAnDxMYLdGu5z" | jq -r '.access_token')" \
  -d @jane-limited-access-model.json | jq -r '.authorization_model_id')

if [ "$MODEL_ID" = "null" ] || [ -z "$MODEL_ID" ]; then
  echo "❌ Failed to create authorization model"
  echo "Response: $(curl -s -X POST http://localhost:8080/stores/$STORE_ID/authorization-models \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $OPENFGA_TOKEN" \
    -d @jane-limited-access-model.fga)"
  exit 1
fi

echo "📝 Model ID: $MODEL_ID"

# Create the authorization tuples
echo "🔐 Creating authorization tuples..."
TUPLES_RESPONSE=$(curl -s -X POST http://localhost:8080/stores/$STORE_ID/authorization-models/$MODEL_ID/write \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENFGA_TOKEN" \
  -d @jane-limited-access-tuples.json)

if [ $? -eq 0 ]; then
    echo "✅ Tuples created successfully"
else
    echo "❌ Failed to create tuples"
    echo "Response: $TUPLES_RESPONSE"
    exit 1
fi

echo "✅ OpenFGA authorization model deployed successfully!"
echo ""
echo "📋 Summary:"
echo "   - Store ID: $STORE_ID"
echo "   - Model ID: $MODEL_ID"
echo "   - User 'irisa' can only access ID and Amount columns"
echo "   - Other service accounts maintain full access"
echo "   - Fine-grained authorization is now active"
echo ""
echo "🌐 You can now access:"
echo "   - Keycloak Admin: http://localhost:30080"
echo "   - Lakekeeper API: http://localhost:8181" 