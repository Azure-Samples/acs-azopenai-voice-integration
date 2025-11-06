# Rendering Order Fix - Agent Text BEFORE UI Components

## Problem

UI components (product carousel, plan options, etc.) were appearing **BEFORE** the agent's spoken text in the transcript, when they should appear **AFTER**.

### Why This Was Happening

When the AI agent calls a tool function:

1. **Tool call is stored** in Cosmos DB immediately (Timestamp T1)
2. **Agent speaks** about showing the options (happens during/after tool call)
3. **Agent text is stored** in Cosmos DB when complete (Timestamp T2)

Because the tool call is stored first, it appears first in the transcript array:
```javascript
transcript = [
  { sender: 'tool_call', message: '...' },      // Position 0 - stored first
  { sender: 'agent', message: 'Let me show...' }, // Position 1 - stored after
  ...
]
```

## Solution

**New Rendering Logic:**

1. **Skip tool_call messages** during normal rendering
2. When rendering **agent/assistant messages**, look backward for any tool_call in the previous 3 messages
3. If found, render the tool_call UI component **AFTER** the agent message
4. Check that there's no intermediate agent message (to avoid rendering the same tool call multiple times)

### Code Implementation

```javascript
{transcript.map((message, index) => {
  // Skip tool_call messages - they'll be rendered after agent messages
  if (message.sender === 'tool_call') {
    return null;
  }
  
  // Render regular message
  const messageElement = (
    <div>Agent/User Message</div>
  );

  // For agent messages, look for preceding tool_call
  let toolCallElement = null;
  if (message.sender === 'agent' || message.sender === 'assistant') {
    // Look back up to 3 messages
    for (let i = Math.max(0, index - 3); i < index; i++) {
      if (transcript[i].sender === 'tool_call') {
        // Check no intermediate agent message
        const hasIntermediateAgentMessage = transcript
          .slice(i + 1, index)
          .some(m => m.sender === 'agent' || m.sender === 'assistant');
        
        if (!hasIntermediateAgentMessage) {
          // This is the first agent message after tool call
          toolCallElement = <div>{renderToolCall(toolData)}</div>;
          break;
        }
      }
    }
  }

  // Return agent message THEN tool UI
  return (
    <React.Fragment key={index}>
      {messageElement}
      {toolCallElement}
    </React.Fragment>
  );
})}
```

## Result

### Correct Order in UI:

```
1. User: "Show me some phones"

2. Agent: "Let me show you some options that match your needs..."
   ↓ (Agent text appears FIRST)

3. [Product Carousel UI Component]
   ↓ (UI appears BELOW agent text)

4. User: "Tell me about the iPhone 15 Pro"

5. Agent: "Excellent choice to ask about! The iPhone 15 Pro features..."
   ↓ (Agent text appears FIRST)

6. [Product Details UI Component]
   ↓ (UI appears BELOW agent text)
```

## Visual Flow

**Before Fix:**
```
[Product Carousel] ❌ Wrong - UI appears first
Agent: "Let me show you..."
```

**After Fix:**
```
Agent: "Let me show you..." ✅ Correct - Agent text first
[Product Carousel]             ✅ Correct - UI appears below
```

## How It Works Step-by-Step

### Example: Showing Product Carousel

1. **User speaks:** "Show me some phones for photography"

2. **AI processes request** and decides to call `show_product_carousel` tool

3. **Tool call stored in Cosmos DB:**
   ```
   Transcript[0]: { sender: 'tool_call', timestamp: T1, ... }
   ```

4. **AI speaks:** "Let me show you some great camera phones..."

5. **Agent message stored in Cosmos DB:**
   ```
   Transcript[0]: { sender: 'tool_call', timestamp: T1 }
   Transcript[1]: { sender: 'agent', message: 'Let me show...', timestamp: T2 }
   ```

6. **Frontend fetches transcript**

7. **Rendering happens:**
   - Index 0 (tool_call): Skip, return null
   - Index 1 (agent): 
     - Render agent message: "Let me show..."
     - Look back: Found tool_call at index 0
     - No intermediate agent messages
     - Render ProductCarousel below agent message

8. **User sees:**
   ```
   Agent: "Let me show you some great camera phones..."
   [Product Carousel with iPhone, Samsung, Pixel options]
   ```

## Edge Cases Handled

### Multiple Tool Calls in Sequence

```
Transcript[0]: tool_call (show_products)
Transcript[1]: agent ("Let me show products...")
Transcript[2]: tool_call (show_details)  
Transcript[3]: agent ("Here are the details...")
```

**Rendering:**
- Index 1: Renders agent[1] + tool_call[0]
- Index 3: Renders agent[3] + tool_call[2]

Each tool call is paired with its corresponding agent announcement.

### Tool Call Without Agent Message

```
Transcript[0]: tool_call (orphaned)
Transcript[1]: user message
```

**Rendering:**
- Tool call at index 0: Skipped (no agent message after it within 3 positions)
- Will not render until agent message appears

### Multiple Agent Messages After Tool Call

```
Transcript[0]: tool_call
Transcript[1]: agent ("Showing options...")
Transcript[2]: agent ("As you can see...")
```

**Rendering:**
- Index 1: Renders agent[1] + tool_call[0]
- Index 2: Renders agent[2] only (intermediate agent check prevents re-rendering tool_call)

## Benefits

✅ **Correct Visual Order**: Agent text always appears before UI components  
✅ **Natural Flow**: Matches how humans communicate (announce, then show)  
✅ **Prevents Confusion**: Users see what's being shown before it appears  
✅ **Handles Edge Cases**: Works with multiple tool calls, orphaned calls, etc.  
✅ **Efficient**: Only renders each tool call once  
✅ **Maintainable**: Clear logic that's easy to understand and modify  

## Testing

### Test Case 1: Single Tool Call
```
1. User: "Show phones"
2. Verify: Agent text appears
3. Verify: Product carousel appears BELOW agent text
```

### Test Case 2: Sequential Tool Calls
```
1. User: "Show phones"
2. Verify: Agent text → Product carousel
3. User: "Tell me about iPhone"
4. Verify: Agent text → Product details
5. Verify: Previous carousel still visible above
```

### Test Case 3: Multiple Agent Messages
```
1. User: "Show phones"
2. Verify: Agent says "Let me show..." → Carousel appears
3. Verify: Agent says "You can see several..." → No duplicate carousel
```

## Summary

The new rendering logic ensures that:
1. Tool calls are invisible in the normal render loop
2. Agent messages trigger a "look-back" for associated tool calls
3. Tool call UI components are rendered AFTER their announcement
4. Each tool call is only rendered once
5. The visual order matches the conversation flow

This creates a natural, intuitive user experience where the AI's words precede the visual aids.

