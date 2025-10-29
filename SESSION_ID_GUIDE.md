# Voice Live Session ID Guide

## Overview

The Voice Live API creates a unique session ID for each call. This session ID can be used to:
- Track conversation sessions
- Link session data with call records
- Debug and monitor specific sessions
- Retrieve session-specific analytics

## How Session IDs are Captured

### Automatic Storage

When a Voice Live session is created, the system automatically:
1. Receives the `session.created` event from Azure
2. Extracts the session ID from the event
3. Stores it in memory (`self.session_ids`)
4. Caches it in Redis for persistence

### Storage Key Format

Session IDs are stored in Redis with the key:
```
voice_live_session_id:{call_id}
```

## Accessing Session IDs

### Method 1: From the Service (Programmatic)

Both `AsyncAzureVoiceLiveService` (non-agent) and `AsyncAzureVoiceLiveAgentService` (agent) have a `get_session_id()` method:

```python
# In your code
session_id = await self.ai_voice_service.get_session_id(call_id)
print(f"Session ID: {session_id}")

# Or for agent mode
session_id = await self.ai_voice_agent_service.get_session_id(call_id)
```

### Method 2: From Redis Cache

You can also retrieve it directly from cache:

```python
from src.services.cache_service import CacheService

cache = CacheService(config)
session_id = await cache.get(f"voice_live_session_id:{call_id}")
```

### Method 3: From Logs

The session ID is automatically logged when the session is created:

```
Session created: sess_abc123xyz456
```

## Example: Adding Session ID to API Response

### Update the Outbound Call Handler

Edit `/api/src/core/app.py`:

```python
async def initiate_outbound_call(self):
    """Initiate an outbound call"""
    # ... existing code ...
    
    # After call is created and connection established
    # Wait briefly for session to be created
    await asyncio.sleep(2)
    
    # Get the session ID
    use_agent = payload_dict.get("use_agent", False)
    if use_agent:
        session_id = await self.ai_voice_agent_service.get_session_id(str(guid))
    else:
        session_id = await self.ai_voice_service.get_session_id(str(guid))
    
    return Response(
        response=json.dumps({
            "call_connection_id": call_connection_id,
            "session_id": session_id,
            "status": "initiated"
        }),
        status=StatusCodes.OK,
        headers={"Content-Type": "application/json"}
    )
```

### Create a New Endpoint to Get Session ID

Add to `/api/src/core/app.py`:

```python
@self.app.route('/api/getSessionId/<call_id>', methods=['GET'])
async def get_session_id(call_id: str):
    """Get the Voice Live session ID for a call"""
    try:
        # Try non-agent service first
        session_id = await self.ai_voice_service.get_session_id(call_id)
        
        # If not found, try agent service
        if not session_id:
            session_id = await self.ai_voice_agent_service.get_session_id(call_id)
        
        if session_id:
            return Response(
                response=json.dumps({
                    "call_id": call_id,
                    "session_id": session_id
                }),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"}
            )
        else:
            return Response(
                response=json.dumps({
                    "error": "Session ID not found",
                    "call_id": call_id
                }),
                status=StatusCodes.NOT_FOUND,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        return Response(
            response=json.dumps({
                "error": str(e)
            }),
            status=StatusCodes.SERVER_ERROR,
            headers={"Content-Type": "application/json"}
        )
```

### Usage

```http
GET http://localhost:8000/api/getSessionId/your-call-id-here
```

Response:
```json
{
    "call_id": "abc-123-def-456",
    "session_id": "sess_xyz789abc123"
}
```

## Session ID Lifecycle

1. **Creation**: Session ID is created when Voice Live WebSocket connects
2. **Storage**: Stored in memory and Redis immediately after `session.created` event
3. **Access**: Available throughout the call duration
4. **Cleanup**: Automatically removed from memory and cache when call ends

## Use Cases

### 1. Link Session to Call Record in CosmosDB

```python
# When storing call data
call_record = {
    "call_id": call_id,
    "session_id": session_id,
    "customer_name": customer_name,
    "timestamp": datetime.now(),
    "transcript": transcript
}
await cosmosdb_service.create_session(call_record)
```

### 2. Debug Specific Sessions

```python
# In your logs
self.logger.info(f"Processing call {call_id}, session {session_id}")
```

### 3. Analytics and Reporting

```python
# Query calls by session ID
sessions = await cosmosdb_service.query_by_session_id(session_id)
```

## Notes

- Session IDs are unique per Voice Live connection
- They persist for the duration of the WebSocket connection
- Format: `sess_` followed by alphanumeric characters
- Session IDs are different from Call Connection IDs
- Available in both agent and non-agent modes

## Troubleshooting

**Session ID is None:**
- The session might not have been created yet (wait 1-2 seconds after call connects)
- Check logs for "Session created:" message
- Verify the WebSocket connection was successful

**Session ID not in cache:**
- Redis might not be running
- Check `REDIS_URL` and `REDIS_PASSWORD` in `.env`
- Verify cache service is initialized

