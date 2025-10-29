#!/bin/bash

# List all agents in Azure OpenAI resource
# Usage: ./list_agents.sh

cd "$(dirname "$0")"

# Load environment variables
source .env 2>/dev/null || { echo "Error: .env file not found"; exit 1; }

# Extract API key (remove quotes)
API_KEY=$(echo "$AZURE_VOICE_LIVE_API_KEY" | tr -d '"')
ENDPOINT=$(echo "$AZURE_VOICE_LIVE_ENDPOINT" | tr -d '"' | sed 's:/$::')

echo "🔍 Listing all agents in Azure OpenAI resource..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make API call
curl -s "${ENDPOINT}/openai/assistants?api-version=2024-05-01-preview" \
  -H "api-key: $API_KEY" | jq -r '
  if .data | length == 0 then
    "❌ No agents found in this resource."
  else
    .data[] | "
    🤖 \(.name // "Unnamed Agent")
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ID:           \(.id)
    Model:        \(.model)
    Instructions: \(.instructions // "None")
    Created:      \(.created_at | strftime("%Y-%m-%d %H:%M:%S"))
    "
  end
'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Done"

