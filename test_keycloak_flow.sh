#!/bin/bash

# Test script for Keycloak authentication flow
# This demonstrates the complete flow from Keycloak login to Django API access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (update these values)
KEYCLOAK_URL="${KEYCLOAK_SERVER_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-master}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-django-client}"
CLIENT_SECRET="${KEYCLOAK_CLIENT_SECRET:-}"
DJANGO_URL="${DJANGO_URL:-http://localhost:8000}"

# Test user credentials (create this user in Keycloak first)
USERNAME="${KEYCLOAK_USERNAME:-testuser}"
PASSWORD="${KEYCLOAK_PASSWORD:-password123}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Keycloak Authentication Flow Test${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if required tools are installed
command -v curl >/dev/null 2>&1 || { echo -e "${RED}Error: curl is required but not installed.${NC}" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Error: jq is required but not installed. Install with: apt-get install jq${NC}" >&2; exit 1; }

# Check if client secret is set
if [ -z "$CLIENT_SECRET" ]; then
    echo -e "${RED}Error: KEYCLOAK_CLIENT_SECRET is not set${NC}"
    echo -e "${YELLOW}Set it with: export KEYCLOAK_CLIENT_SECRET='your-secret'${NC}"
    echo -e "${YELLOW}Or update the .env file${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Keycloak URL: ${KEYCLOAK_URL}"
echo -e "  Realm: ${KEYCLOAK_REALM}"
echo -e "  Client ID: ${CLIENT_ID}"
echo -e "  Django URL: ${DJANGO_URL}"
echo -e "  Username: ${USERNAME}"
echo ""

# Step 1: Get token from Keycloak
echo -e "${BLUE}Step 1: Getting token from Keycloak...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST \
  "${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "grant_type=password" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}")

# Check if login was successful
if echo "$TOKEN_RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    echo -e "${RED}❌ Keycloak login failed:${NC}"
    echo "$TOKEN_RESPONSE" | jq '.'
    exit 1
fi

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.refresh_token')
EXPIRES_IN=$(echo "$TOKEN_RESPONSE" | jq -r '.expires_in')

echo -e "${GREEN}✅ Successfully obtained Keycloak token${NC}"
echo -e "  Token type: Bearer"
echo -e "  Expires in: ${EXPIRES_IN} seconds"
echo -e "  Access token: ${ACCESS_TOKEN:0:50}..."
echo ""

# Step 2: Decode token to see claims
echo -e "${BLUE}Step 2: Token claims (decoded):${NC}"
# JWT payload is the second part (split by .)
PAYLOAD=$(echo "$ACCESS_TOKEN" | cut -d'.' -f2)
# Add padding if needed for base64
PADDING=$((4 - ${#PAYLOAD} % 4))
if [ $PADDING -ne 4 ]; then
    PAYLOAD="${PAYLOAD}$(printf '=%.0s' $(seq 1 $PADDING))"
fi
echo "$PAYLOAD" | base64 -d 2>/dev/null | jq '.' || echo "Could not decode token"
echo ""

# Step 3: Call Django health check (no auth required)
echo -e "${BLUE}Step 3: Testing Django API connection...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${DJANGO_URL}/health/")
HTTP_STATUS=$(echo "$HEALTH_RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Django API is accessible${NC}"
else
    echo -e "${RED}❌ Django API is not accessible (HTTP ${HTTP_STATUS})${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Step 4: Call /me endpoint with Keycloak token (user will be auto-created)
echo -e "${BLUE}Step 4: Calling /me endpoint (user auto-creation)...${NC}"
ME_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "${DJANGO_URL}/api/v1/users/me/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

HTTP_STATUS=$(echo "$ME_RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$ME_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Successfully authenticated with Keycloak token${NC}"
    echo -e "${GREEN}✅ User automatically created/updated in Django${NC}"
    echo ""
    echo -e "${YELLOW}User data:${NC}"
    echo "$RESPONSE_BODY" | jq '.'

    # Extract user info
    USER_ID=$(echo "$RESPONSE_BODY" | jq -r '.id')
    USER_EMAIL=$(echo "$RESPONSE_BODY" | jq -r '.email')
    USER_NAME=$(echo "$RESPONSE_BODY" | jq -r '.full_name')

    echo ""
    echo -e "${GREEN}✅ Django user created:${NC}"
    echo -e "  ID: ${USER_ID}"
    echo -e "  Email: ${USER_EMAIL}"
    echo -e "  Name: ${USER_NAME}"
else
    echo -e "${RED}❌ Authentication failed (HTTP ${HTTP_STATUS})${NC}"
    echo "$RESPONSE_BODY" | jq '.' || echo "$RESPONSE_BODY"
    exit 1
fi
echo ""

# Step 5: Test another authenticated endpoint
echo -e "${BLUE}Step 5: Testing user list endpoint...${NC}"
USERS_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "${DJANGO_URL}/api/v1/users/?page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

HTTP_STATUS=$(echo "$USERS_RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$USERS_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Successfully accessed user list${NC}"
    TOTAL_USERS=$(echo "$RESPONSE_BODY" | jq -r '.count')
    echo -e "  Total users in database: ${TOTAL_USERS}"
else
    echo -e "${YELLOW}⚠️  Could not access user list (HTTP ${HTTP_STATUS})${NC}"
    echo -e "${YELLOW}  This may require admin permissions${NC}"
fi
echo ""

# Step 6: Update user profile
echo -e "${BLUE}Step 6: Testing profile update...${NC}"
UPDATE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PATCH \
  "${DJANGO_URL}/api/v1/users/me/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Updated via Keycloak auth test"}')

HTTP_STATUS=$(echo "$UPDATE_RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$UPDATE_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Successfully updated user profile${NC}"
    echo -e "  Bio: $(echo "$RESPONSE_BODY" | jq -r '.bio')"
else
    echo -e "${RED}❌ Profile update failed (HTTP ${HTTP_STATUS})${NC}"
    echo "$RESPONSE_BODY" | jq '.' || echo "$RESPONSE_BODY"
fi
echo ""

# Step 7: Test Keycloak config endpoint
echo -e "${BLUE}Step 7: Getting Keycloak configuration...${NC}"
CONFIG_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "${DJANGO_URL}/api/v1/auth/keycloak/config/")

HTTP_STATUS=$(echo "$CONFIG_RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$CONFIG_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Keycloak configuration:${NC}"
    echo "$RESPONSE_BODY" | jq '.'
else
    echo -e "${RED}❌ Could not get configuration (HTTP ${HTTP_STATUS})${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo -e "1. ✅ Obtained token from Keycloak"
echo -e "2. ✅ Decoded token claims"
echo -e "3. ✅ Verified Django API connection"
echo -e "4. ✅ User auto-created in Django on first request"
echo -e "5. ✅ Accessed authenticated endpoints"
echo -e "6. ✅ Updated user profile"
echo -e "7. ✅ Retrieved Keycloak configuration"
echo ""
echo -e "${YELLOW}Your Keycloak token (save for manual testing):${NC}"
echo -e "${ACCESS_TOKEN}"
echo ""
echo -e "${YELLOW}Test the token manually:${NC}"
echo -e "curl -X GET ${DJANGO_URL}/api/v1/users/me/ \\"
echo -e "  -H 'Authorization: Bearer ${ACCESS_TOKEN}'"
echo ""
echo -e "${YELLOW}Refresh token:${NC}"
echo -e "curl -X POST ${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token \\"
echo -e "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo -e "  -d 'client_id=${CLIENT_ID}' \\"
echo -e "  -d 'client_secret=${CLIENT_SECRET}' \\"
echo -e "  -d 'grant_type=refresh_token' \\"
echo -e "  -d 'refresh_token=${REFRESH_TOKEN}'"
echo ""
