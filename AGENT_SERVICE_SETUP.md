# Azure AI Foundry Agent Service Setup Guide

This guide explains how to set up and use Azure AI Foundry Agent Service with your Voice Live application.

## Overview

The application now supports **two modes** for voice live conversations:

1. **Non-Agent Mode** (Default): Direct connection to Azure Voice Live API
2. **Agent Mode**: Uses Azure AI Foundry Agent Service for managed agent conversations

## Prerequisites

### For Agent Mode

1. **Azure AI Foundry Resource** - Created in a supported region
2. **Azure AI Foundry Project** - Set up in the Azure AI Foundry portal
3. **Azure AI Foundry Agent** - Created and configured with your desired conversation flow
4. **Agent Access Token** - Authentication token for accessing the agent

> **Note**: You don't need to deploy an audio model separately. Voice Live is fully managed.

## Environment Variables

Add these variables to your `.env` file:

### Required for All Modes

```env
# Azure Communication Services
ACS_CONNECTION_STRING=your_acs_connection_string
COGNITIVE_SERVICE_ENDPOINT=your_cognitive_services_endpoint
AGENT_PHONE_NUMBER=your_agent_phone_number

# Azure OpenAI / Voice Live
AZURE_VOICE_LIVE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VOICE_LIVE_DEPLOYMENT=gpt-4o
AZURE_VOICE_LIVE_API_VERSION=2025-10-01
AZURE_VOICE_LIVE_API_KEY=your_api_key

# Callback Configuration
CALLBACK_URI_HOST=https://your-public-url.com

# Redis Cache
REDIS_URL=your_redis_url
REDIS_PASSWORD=your_redis_password

# CosmosDB
COSMOS_DB_URL=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DB_KEY=your_cosmos_key
COSMOS_DB_DATABASE_NAME=your_database_name
COSMOS_DB_CONTAINER_NAME=your_container_name
```

### Required for Agent Mode Only

```env
# AI Foundry Agent Service
AI_FOUNDRY_PROJECT_NAME=your_project_name
AI_FOUNDRY_AGENT_ID=your_agent_id
AI_FOUNDRY_AGENT_ACCESS_TOKEN=your_agent_access_token
```

## How to Get Agent Credentials

### 1. Create Azure AI Foundry Resource

```bash
# Via Azure Portal
# Navigate to Azure AI Foundry → Create Resource
# Select a supported region (check documentation for latest list)
```

### 2. Create an Agent in Azure AI Foundry Portal

1. Go to [Azure AI Foundry Portal](https://ai.azure.com)
2. Navigate to your project
3. Select **Agents** from the left menu
4. Click **Create Agent**
5. Configure:
   - Agent name
   - Instructions/Prompt
   - Model settings
   - Tools and capabilities
6. Save and note the **Agent ID**

### 3. Get Agent Access Token

The agent access token can be obtained via:

**Option 1: Azure Portal**
- Navigate to your AI Foundry resource
- Go to **Keys and Endpoint**
- Copy the access key

**Option 2: Azure CLI**
```bash
az cognitiveservices account keys list \
  --name your-resource-name \
  --resource-group your-resource-group
```

**Option 3: Azure Identity SDK** (Recommended for production)
```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")
```

## Usage

### Making Calls with REST API

The `outbound_call.http` file now includes examples for both modes.

#### Non-Agent Mode (Default)

```http
POST http://localhost:8000/api/initiateOutboundCall
Content-Type: application/json

{
    "phone_number": "+1234567890",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "use_agent": false
}
```

#### Agent Mode

```http
POST http://localhost:8000/api/initiateOutboundCall
Content-Type: application/json

{
    "phone_number": "+1234567890",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "use_agent": true
}
```

### Programmatic Usage

```python
import requests

# Non-Agent Mode
response = requests.post(
    "http://localhost:8000/api/initiateOutboundCall",
    json={
        "phone_number": "+1234567890",
        "customer_name": "John Doe",
        "use_agent": False  # or omit for default
    }
)

# Agent Mode
response = requests.post(
    "http://localhost:8000/api/initiateOutboundCall",
    json={
        "phone_number": "+1234567890",
        "customer_name": "John Doe",
        "use_agent": True  # Enable agent mode
    }
)
```

## Architecture

### Non-Agent Mode Flow

```
Phone Call → ACS → WebSocket → AsyncAzureVoiceLiveService → Voice Live API
```

### Agent Mode Flow

```
Phone Call → ACS → WebSocket → AsyncAzureVoiceLiveAgentService → Voice Live API (with Agent)
```

## Key Differences

| Feature | Non-Agent Mode | Agent Mode |
|---------|---------------|------------|
| Configuration | In code via `session_config()` | Managed in Azure AI Foundry portal |
| Prompts | Specified in application | Managed within the agent |
| Tools/Functions | Defined in code | Configured in agent |
| Updates | Requires code changes | Update in portal, no deployment needed |
| Complexity | Direct API calls | Agent abstracts complexity |
| Scalability | Manual management | Built-in agent orchestration |

## Benefits of Agent Mode

1. **Separation of Concerns**: Business logic in agent, code handles communication
2. **Easier Updates**: Modify agent behavior without code changes
3. **Better Management**: Centralized agent configuration
4. **Advanced Features**: Leverage agent-specific capabilities (tool calling, memory, etc.)
5. **Multi-tenant Support**: Different agents for different use cases

## Troubleshooting

### Agent Mode Not Working

1. **Check Environment Variables**
   ```bash
   echo $AI_FOUNDRY_PROJECT_NAME
   echo $AI_FOUNDRY_AGENT_ID
   echo $AI_FOUNDRY_AGENT_ACCESS_TOKEN
   ```

2. **Verify Agent Exists**
   - Log into Azure AI Foundry portal
   - Check that the agent ID matches

3. **Check Logs**
   ```
   # Look for:
   "Using Agent Service for call {call_id}"
   # vs
   "Using Non-Agent Service for call {call_id}"
   ```

4. **Test Agent Connection**
   ```bash
   # Test in Speech Playground first
   # Azure AI Foundry Portal → Playgrounds → Speech → Voice Live
   ```

### Common Errors

**"Agent access token is required"**
- Solution: Set `AI_FOUNDRY_AGENT_ACCESS_TOKEN` in `.env`

**"Agent ID and Project Name are required for agent mode"**
- Solution: Set `AI_FOUNDRY_AGENT_ID` and `AI_FOUNDRY_PROJECT_NAME`

**"Failed to connect to Voice Live Agent API"**
- Check your endpoint URL
- Verify API version compatibility
- Ensure agent exists in the specified project

## References

- [Azure AI Foundry Agent Service Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-agents-quickstart)
- [Voice Live API Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-overview)
- [Create an Agent Quickstart](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/create-agent)

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test with non-agent mode first to isolate issues
4. Review Azure AI Foundry portal for agent status

