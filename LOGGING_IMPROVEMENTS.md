# Logging Improvements

## Changes Made

### 1. ✅ Session ID Now Printed to Console

When a Voice Live session is created, you'll now see a prominent console message:

**Non-Agent Mode:**
```
🎯 SESSION ID: sess_abc123xyz456 | Call ID: 1234-5678-90ab-cdef
```

**Agent Mode:**
```
🎯 AGENT SESSION ID: sess_xyz789abc123 | Call ID: 1234-5678-90ab-cdef
```

**When it appears:**
- Automatically printed when the Voice Live WebSocket connection establishes
- Appears within 1-2 seconds of the call connecting
- Visible in both terminal and logs

### 2. ✅ Reduced WebSocket Error Spam

**Before:**
```
2025-10-23 01:06:43,339 - ERROR - Error processing WebSocket message: WebSocket not connected
2025-10-23 01:06:43,358 - ERROR - Error processing WebSocket message: WebSocket not connected
2025-10-23 01:06:43,379 - ERROR - Error processing WebSocket message: WebSocket not connected
2025-10-23 01:06:43,397 - ERROR - Error processing WebSocket message: WebSocket not connected
2025-10-23 01:06:43,421 - ERROR - Error processing WebSocket message: WebSocket not connected
... (hundreds more)
```

**After:**
```
[No repeated error messages - cleaner console!]
```

**What was changed:**
- "WebSocket not connected" errors are now silently ignored
- Only unexpected/genuine errors are logged
- Applies to all three voice services:
  - `ai_voice_service.py` (non-agent mode)
  - `ai_voice_agent_service.py` (agent mode)
  - `openai_realtime_service.py` (legacy)

## Files Modified

### 1. `api/src/services/ai_voice_service.py`
- **Line 149**: Added session ID console print
- **Lines 246-248**: Filtered WebSocket error logging

### 2. `api/src/services/ai_voice_agent_service.py`
- **Line 282**: Added agent session ID console print
- **Lines 384-386**: Filtered WebSocket error logging

### 3. `api/src/services/openai_realtime_service.py`
- **Lines 179-181**: Filtered WebSocket error logging

## Benefits

### Cleaner Console Output
- No more scrolling through hundreds of identical error messages
- Important logs are now visible and easy to find
- Error logs only show genuine issues that need attention

### Session ID Visibility
- Easy to spot session IDs at a glance
- Emoji (🎯) makes it stand out
- Helpful for debugging and tracking specific calls
- Can copy/paste session ID for queries or analysis

### Better Debugging Experience
- Console remains readable during calls
- Real issues are easier to identify
- Session tracking is straightforward

## Usage Examples

### Viewing Session ID in Terminal

```bash
# Start your API server
python api/main.py

# Make a call
# Watch for the session ID to appear:

🎯 SESSION ID: sess_abc123xyz456 | Call ID: c3be73f0-bf4c-4e74-83e1-38e7c011478f
```

### Tracking Session ID

You can now easily:
1. **Copy the session ID** from console
2. **Query it in CosmosDB** for call history
3. **Use it for analytics** or debugging
4. **Reference it in support tickets**

### What You'll See

**Normal Operation:**
```
2025-10-23 01:01:11,817 - INFO - Received CallConnected event
2025-10-23 01:01:11,818 - INFO - Starting audio playback ...

🎯 SESSION ID: sess_abc123xyz456 | Call ID: c3be73f0-bf4c-4e74-83e1-38e7c011478f

2025-10-23 01:01:12,120 - INFO - >>> User: Hello, I'm looking for travel advice
2025-10-23 01:01:13,450 - INFO - >>> Agent: Hello! I'd be happy to help...
```

**Agent Fallback (Clean):**
```
2025-10-23 01:01:11,956 - WARNING - Agent Service failed for call xyz: 500 error
2025-10-23 01:01:11,957 - INFO - Falling back to Non-Agent Service for call xyz

🎯 SESSION ID: sess_abc123xyz456 | Call ID: xyz

[Call continues successfully in non-agent mode - no error spam!]
```

## Additional Notes

### Why Filter "WebSocket not connected"?

This error typically occurs when:
- Agent mode fails and falls back to non-agent mode
- The agent WebSocket closes before ACS audio stops
- This is expected behavior during fallback
- Logging it hundreds of times adds no value

### Why Not Filter All Errors?

We only filter this specific error because:
- Other WebSocket errors might indicate real issues
- "WebSocket not connected" is the only error that repeats excessively
- We still want to see genuine connection problems

### Session ID Emoji

The 🎯 emoji was chosen because:
- Easy to spot in large log files
- Visually distinct from other log entries
- Universally supported in modern terminals
- Represents "targeting" a specific session

## Troubleshooting

**Session ID not appearing:**
- Make sure the call actually connected (check for "CallConnected" event)
- Wait 2-3 seconds after call initiation
- Check that Voice Live WebSocket established successfully

**Still seeing error spam:**
- Restart your API server to load the changes
- Verify you're running the latest code
- Check that the error message is exactly "WebSocket not connected"

**Want to see filtered errors:**
- Temporarily remove the filter in the code:
```python
# Comment out the filter
# if "WebSocket not connected" not in str(e):
self.logger.error(f'Error processing WebSocket message: {e}')
```

