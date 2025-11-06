# Vodafone Sales Agent with Interactive Tools - Feature Guide

## Overview

This feature implements an AI-powered Vodafone sales agent that can display interactive UI components during voice conversations. When the AI agent needs to show products or plans, it uses OpenAI's function calling (tools) to trigger visual elements in the web UI where customers can make selections.

## Architecture

### Backend Components

1. **New Persona in `constants.py`**
   - `SYSTEM_MESSAGE_VODAFONE_SALES`: Comprehensive prompt for a Vodafone sales agent named "Emma"
   - Agent is instructed to use specific tools to show products and plans
   - Added to `system_message_dict` with key `"vodafone_sales"`

2. **Tool Definitions in Session Configuration**
   - Added to both `ai_voice_service.py` and `ai_voice_agent_service.py`
   - Three tools available:
     - `show_product_carousel`: Display multiple products for browsing
     - `show_product_details`: Show detailed specs for a specific product
     - `show_plan_options`: Display available monthly plans
   - `tool_choice: "auto"`: AI decides when to call tools

3. **Tool Call Handling**
   - Both services listen for `response.function_call_arguments.done` events
   - Tool calls are stored in Cosmos DB with sender type `"tool_call"`
   - Tool response endpoint at `/api/tool_response` allows UI to send selections back to AI

### Frontend Components

1. **Product Data (`ui/src/data/products.js`)**
   - Complete catalog of phones, tablets, and plans
   - Product details, pricing, features, images
   - Helper functions to filter products by category, price, tags

2. **Interactive UI Components**
   - **ProductCarousel**: Grid view of filtered products with selection
   - **ProductDetails**: Detailed view with specs and storage options
   - **PlanOptions**: Monthly plan selection with contract length

3. **TranscriptViewer Updates**
   - Detects `tool_call` messages in conversation
   - Renders appropriate interactive component based on function name
   - Handles user selections and sends responses back via API

## How It Works

### 1. Conversation Flow

```
User calls Vodafone → AI Agent answers → Discovery phase
                                              ↓
User expresses interest (e.g., "I need a new phone for photography")
                                              ↓
AI Agent: "Let me show you some great camera phones..."
                                              ↓
AI calls show_product_carousel tool with args:
{
  "category": "phones",
  "filter": "camera-focused",
  "max_price": 1200
}
```

### 2. Tool Call Processing

```
Backend receives tool call event → Stores in Cosmos DB
                                          ↓
                                  Frontend polls transcript
                                          ↓
                              Detects tool_call message
                                          ↓
                              Renders ProductCarousel
```

### 3. User Selection & Response

```
User selects iPhone 15 Pro (256GB) in UI → onClick handler
                                                  ↓
                                    Frontend calls /api/tool_response
                                                  ↓
Backend receives tool response → Sends to OpenAI Realtime API
                                                  ↓
                              AI acknowledges: "Excellent choice! 
                              The iPhone 15 Pro has an amazing camera system..."
```

## Usage Example

### Starting a Vodafone Sales Call

1. In the UI, select persona: `"Vodafone Sales"`
2. Enter customer phone number
3. Use agent mode: `true` (recommended)
4. Initiate call

### Sample Conversation

**AI Agent**: "Hi! I'm Emma, a Vodafone AI sales assistant. I'd love to help you find the perfect device today. What are you looking for?"

**Customer**: "I need a phone for taking lots of photos, budget around £1000"

**AI Agent**: "Perfect! Let me show you some excellent options..."
*[ProductCarousel appears in UI showing camera-focused phones]*

**Customer**: *[Selects iPhone 15 Pro, 256GB]*

**AI Agent**: "Excellent choice! The iPhone 15 Pro has an incredible camera system with 48MP sensor. Would you like to see the available plans for this device?"

**Customer**: "Yes please"

**AI Agent**: "Let me display the plan options..."
*[PlanOptions component appears showing monthly plans]*

## Key Features

### For the AI Agent
- Natural language understanding of customer needs
- Automatic tool calling when appropriate
- Receives structured data from customer selections
- Can discuss products after selection

### For the Customer
- Visual product browsing during voice call
- Easy comparison of specs and prices
- Interactive selection without verbal communication
- Smooth handoff back to voice conversation

### For Developers
- Easy to extend with new products (just update `products.js`)
- New tools can be added by:
  1. Adding tool definition to session config
  2. Creating React component
  3. Adding case to `renderToolCall` in TranscriptViewer
- Tool responses are automatically handled

## Tool Response Format

When a user makes a selection, the frontend sends:

```json
{
  "session_id": "call_connection_id",
  "tool_call_id": "call_abc123",
  "result": {
    "product_id": "iphone-15-pro",
    "product_name": "iPhone 15 Pro",
    "storage": "256GB",
    "price": "£1,199"
  },
  "use_agent_mode": true
}
```

The AI receives this as tool output and continues the conversation naturally.

## Testing

### Backend Testing
```bash
# Start the backend
cd api
python main.py
```

### Frontend Testing
```bash
# Start the UI
cd ui
npm run dev
```

### Full Integration Test
1. Initiate call with `"vodafone_sales"` persona
2. During conversation, say "show me some phones"
3. Verify ProductCarousel appears in transcript
4. Select a product
5. Verify AI acknowledges selection
6. Continue conversation

## Extending the Feature

### Adding a New Product

```javascript
// In ui/src/data/products.js
"new-product": {
  id: "new-product",
  name: "Product Name",
  brand: "Brand",
  category: "phones",
  image: "https://...",
  basePrice: 599,
  storageOptions: {
    "64GB": { price: 599, displayPrice: "£599" }
  },
  features: ["Feature 1", "Feature 2"],
  tags: ["budget"]
}
```

### Adding a New Tool

1. **Define in session config** (`ai_voice_service.py`):
```python
{
    "type": "function",
    "name": "show_accessories",
    "description": "Display phone accessories like cases and chargers",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {"type": "string"}
        }
    }
}
```

2. **Create React component**:
```jsx
// ui/src/components/AccessoriesView.jsx
const AccessoriesView = ({ productId, onSelect, toolCallId }) => {
  // Component implementation
};
```

3. **Add to renderToolCall** in TranscriptViewer:
```jsx
case 'show_accessories':
  return <AccessoriesView productId={args.product_id} ... />;
```

## Benefits

1. **Enhanced Customer Experience**: Visual aids during voice calls
2. **Reduced Cognitive Load**: Easier to compare options visually
3. **Higher Conversion**: Interactive elements encourage decisions
4. **Flexibility**: AI decides when to show UI vs. just talking
5. **Scalability**: Easy to add new products and tools

## Future Enhancements

- Real-time inventory checking
- Personalized recommendations based on purchase history
- Integration with actual Vodafone product API
- Checkout and payment processing
- Order tracking UI
- Support for video calls to show products physically

