# AI Silence Detection & Automatic Recovery

## Overview

This feature automatically detects when the AI agent goes silent after a user stops speaking and triggers a fallback response to keep the conversation flowing naturally.

## Problem Solved

**Before:** AI agent would sometimes go silent after user speaks, creating awkward pauses and requiring user to probe repeatedly.

**After:** System automatically detects silence within 3 seconds and triggers the AI to respond.

## How It Works

### 1. Timer Management

The service tracks a silence timer for each active call:

```python
self.silence_timers = {}  # Track silence detection timers for each call
self.silence_threshold = 3.0  # 3 seconds threshold
```

### 2. Event-Driven Detection

The system monitors OpenAI Realtime API events:

```
User speaks: "Show me some phones"
  ↓
Event: input_audio_buffer.speech_stopped
  ↓
Action: Start 3-second timer ⏰
  ↓
[Waiting for AI response...]
  ↓
Two Possible Outcomes:
  
  A) AI responds within 3 seconds ✅
     Event: response.audio.delta
     Action: Cancel timer
     Result: Normal conversation flow
  
  B) 3 seconds pass with no response ⚠️
     Timer expires
     Action: Trigger fallback response
     Result: AI forced to respond
```

### 3. Timer Lifecycle

**Start Timer:**
- Triggered by: `input_audio_buffer.speech_stopped`
- Means: User finished their sentence
- Action: Start counting down from 3 seconds

**Cancel Timer:**
- Triggered by:
  - `response.audio.delta` (AI starts speaking)
  - `response.audio_transcript.delta` (AI generating response)
  - `input_audio_buffer.speech_started` (User speaks again)
- Means: AI is responding or user interrupted
- Action: Stop and remove timer

**Timer Expires:**
- After: 3 seconds of silence
- Action: Call `_handle_silence_fallback()`
- Result: Force AI to generate response

## Implementation Details

### 1. Start Silence Timer

```python
async def _start_silence_timer(self, call_id: str):
    """Start a timer to detect AI silence after user stops speaking"""
    # Cancel any existing timer
    await self._cancel_silence_timer(call_id)
    
    async def silence_timeout():
        try:
            await asyncio.sleep(self.silence_threshold)
            # Timer expired - AI hasn't responded
            self.logger.warning(f"⚠️ AI Silence detected for call {call_id}")
            await self._handle_silence_fallback(call_id)
        except asyncio.CancelledError:
            # Timer was cancelled - AI responded in time
            pass
    
    # Create and store the timer task
    timer_task = asyncio.create_task(silence_timeout())
    self.silence_timers[call_id] = timer_task
```

### 2. Cancel Silence Timer

```python
async def _cancel_silence_timer(self, call_id: str):
    """Cancel the silence detection timer for a call"""
    if call_id in self.silence_timers:
        timer_task = self.silence_timers[call_id]
        if not timer_task.done():
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass
        del self.silence_timers[call_id]
```

### 3. Handle Silence Fallback

```python
async def _handle_silence_fallback(self, call_id: str):
    """Handle AI silence by triggering a fallback response"""
    connection = self.connections.get(call_id)
    if not connection:
        return
    
    # Force the AI to generate a response
    response_create = {
        "type": "response.create"
    }
    await connection.send(message=json.dumps(response_create))
```

## Event Integration

### In `receive_audio_and_playback()`:

```python
# User stopped speaking - start timer
elif event_type == "input_audio_buffer.speech_stopped":
    await self._start_silence_timer(call_id)

# User started speaking - cancel timer
elif event_type == "input_audio_buffer.speech_started":
    await self._cancel_silence_timer(call_id)
    await self.stop_audio(call_id)

# AI responding with audio - cancel timer
elif event_type == "response.audio.delta":
    await self._cancel_silence_timer(call_id)
    await self.oai_to_acs(call_id, event.get("delta", ""))

# AI generating transcript - cancel timer
elif event_type == "response.audio_transcript.delta":
    await self._cancel_silence_timer(call_id)
```

## Cleanup

Timer is automatically cleaned up when call ends:

```python
async def cleanup_call_resources(self, call_id: str, is_acs_id: bool = True):
    # Cancel any active silence timer
    await self._cancel_silence_timer(call_id)
    
    # ... rest of cleanup
```

## Configuration

The silence threshold is configurable in `__init__`:

```python
self.silence_threshold = 3.0  # 3 seconds threshold
```

You can adjust this value:
- **Lower (1-2s)**: More aggressive, triggers faster but may interrupt natural pauses
- **Higher (4-5s)**: More patient, allows longer thinking time but delays recovery

**Recommended:** 3 seconds balances natural conversation flow with quick recovery.

## Logging & Monitoring

### Debug Logs:

```
⏰ Started silence timer for call abc123 (3.0s)
✅ Silence timer cancelled for call abc123 - AI responded
```

### Warning Logs:

```
⚠️ AI Silence detected for call abc123 after 3.0s
🔄 Triggering fallback response for call abc123
```

## Example Scenarios

### Scenario 1: Normal Flow (No Silence)

```
User: "Show me the iPhone 15 Pro details"
  ↓
Event: speech_stopped → Timer starts ⏰
  ↓
(0.5s later)
  ↓
Event: response.audio.delta → Timer cancelled ✅
  ↓
AI: "Let me pull up those details for you..."
```

### Scenario 2: Silence Detected

```
User: "What about the Samsung S24?"
  ↓
Event: speech_stopped → Timer starts ⏰
  ↓
(3.0s later - no AI response)
  ↓
Timer expires ⚠️
  ↓
Fallback: Send response.create
  ↓
AI: "The Samsung S24 Ultra is an excellent choice..."
```

### Scenario 3: User Interrupts

```
User: "Show me some phones"
  ↓
Event: speech_stopped → Timer starts ⏰
  ↓
(1.0s later - before AI responds)
  ↓
User: "Actually, show me tablets instead"
  ↓
Event: speech_started → Timer cancelled ✅
  ↓
New timer starts when user stops again
```

## Benefits

✅ **Automatic Recovery:** No manual intervention needed when AI goes silent  
✅ **Fast Detection:** 3-second threshold is imperceptible to users  
✅ **Natural Flow:** Preserves conversation rhythm  
✅ **Prevents Dead Air:** Eliminates awkward silences  
✅ **User-Friendly:** Users don't need to repeat or probe  
✅ **Efficient:** Uses asyncio for non-blocking timers  
✅ **Clean Cleanup:** Timers properly cancelled and removed  

## Advanced Options

### Option 1: Inject System Message (Currently Commented)

Instead of just sending `response.create`, you can inject a system prompt:

```python
conversation_item = {
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "system",
        "content": [{
            "type": "input_text", 
            "text": "Please respond to the user's last message."
        }]
    }
}
await connection.send(message=json.dumps(conversation_item))
await connection.send(message=json.dumps({"type": "response.create"}))
```

### Option 2: Context-Aware Fallback

You could make the fallback context-aware:

```python
# After tool calls
if "tool_call" in recent_events:
    prompt = "Please continue by describing the options shown to the user."

# After user question
else:
    prompt = "Please respond to the user's question."
```

### Option 3: Progressive Escalation

```python
silence_count = self.silence_counts.get(call_id, 0)
if silence_count == 0:
    # First silence: Simple retry
    await connection.send(response_create)
elif silence_count == 1:
    # Second silence: Add system message
    await self._inject_system_prompt(call_id)
else:
    # Third+ silence: Log error, possible system issue
    self.logger.error("Multiple silence events - possible AI issue")
```

## Testing

To test silence detection:

1. Start a call
2. Speak to the AI
3. Observe logs:
   - `⏰ Started silence timer` should appear
   - Within 3s, should see `✅ Silence timer cancelled`
4. To trigger fallback:
   - Use a query that might confuse the AI
   - Or temporarily increase threshold to 0.5s for testing

## Summary

The silence detection system:
1. **Monitors** user speech end events
2. **Waits** 3 seconds for AI response
3. **Detects** if AI doesn't respond
4. **Recovers** by forcing AI to generate response
5. **Cleans up** timers properly

This ensures smooth, natural conversations without awkward silences or requiring users to repeatedly probe the AI agent.

