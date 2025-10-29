#!/bin/bash
# Script to test agent endpoint in different regions
# Usage: ./check_agent_support.sh

echo "Checking Voice Live Agent API support..."
echo ""
echo "Your current setup:"
grep "AZURE_VOICE_LIVE_ENDPOINT" .env | sed 's/=/ = /'
echo ""
echo "Testing connection..."

API_KEY=$(grep "AZURE_VOICE_LIVE_API_KEY" .env | cut -d'=' -f2 | tr -d '"')
ENDPOINT=$(grep "AZURE_VOICE_LIVE_ENDPOINT" .env | cut -d'=' -f2 | tr -d '"' | sed 's:/$::')

# Test the endpoint
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  "${ENDPOINT}/voice-live/realtime?api-version=2025-10-01" \
  -H "api-key: $API_KEY"

echo ""
echo "Note: 500 = Endpoint exists but agent feature unavailable"
echo "      404 = Endpoint/feature not found"
echo "      401 = Authentication issue"
