# WebSocket Troubleshooting Guide

## Error: Transport url is not valid or web socket server is not operational

This error (Code 400, Subcode 8581) means Azure Communication Services cannot connect to your WebSocket endpoint.

## Quick Diagnosis

### Step 1: Check Your Dev Tunnel Configuration

**For Azure Dev Tunnels, you MUST enable WebSocket support:**

```bash
# List your tunnels
devtunnel list

# Delete existing tunnel if needed
devtunnel delete <tunnel-id>

# Create a new tunnel WITH WebSocket support
devtunnel create --allow-anonymous

# IMPORTANT: Add port with protocol support
devtunnel port create -p 8000 --protocol https --protocol auto

# Host the tunnel
devtunnel host
```

### Step 2: Verify WebSocket URL Format

Your `.env` file should have:
```bash
CALLBACK_URI_HOST=https://xxxxx-8000.usw2.devtunnels.ms
```

**NOT:**
- ❌ `http://xxxxx...` (must be https)
- ❌ `wss://xxxxx...` (must be https, not wss)
- ❌ `http://localhost:8000` (must be public)

### Step 3: Check Backend Logs

After making a call, check your backend logs for:

```
WebSocket URL for ACS: wss://xxxxx-8000.usw2.devtunnels.ms/ws/<guid>
```

This should show the correct WebSocket URL being sent to ACS.

### Step 4: Verify WebSocket Connection

Run the test script:

```bash
cd /path/to/project
python test_websocket.py
```

Expected output:
```
✅ WebSocket connection successful!
```

If it fails:
```
❌ WebSocket connection failed: ...
```

## Common Issues & Solutions

### Issue 1: Dev Tunnel Doesn't Support WebSockets

**Solution:**
```bash
# Create tunnel with proper protocol support
devtunnel port create -p 8000 --protocol auto
```

The `auto` protocol includes WebSocket support.

### Issue 2: Backend Not Responding to WebSocket

**Check if the WebSocket handler is registered:**

Look for this in your logs when starting the backend:
```python
# Should see WebSocket route registered
```

**Verify manually:**
```bash
# Install wscat if needed
npm install -g wscat

# Test WebSocket connection
wscat -c "wss://your-tunnel-url.devtunnels.ms/ws/test"
```

### Issue 3: HTTPS/WSS Certificate Issues

Dev Tunnels should handle SSL automatically, but if you see certificate errors:

```bash
# Make sure you're using the tunnel URL with -8000 in the subdomain
# Example: https://xxxxx-8000.usw2.devtunnels.ms
```

### Issue 4: Tunnel Not Exposing Port 8000

**Verify tunnel status:**
```bash
devtunnel show

# Should see:
# Port 8000
# Protocol: auto
# Access: public
```

## Alternative: Using ngrok

If Dev Tunnels continue to have issues, try ngrok:

```bash
# Install ngrok
brew install ngrok

# Start tunnel
ngrok http 8000

# Copy the HTTPS URL (not HTTP)
# Example: https://xxxx-xx-xx.ngrok-free.app

# Update .env
CALLBACK_URI_HOST=https://xxxx-xx-xx.ngrok-free.app
```

## Debugging Steps

1. **Restart your backend** after changing `.env`:
   ```bash
   # Kill existing process
   pkill -f "python.*main.py"
   
   # Restart
   python api/main.py
   ```

2. **Check the logs** when initiating a call:
   - Should see: `WebSocket URL for ACS: wss://...`
   - Should see: `🔌 WebSocket connection attempt for call ...`
   
3. **If you see the WebSocket URL but NO connection attempt:**
   - Issue is with tunnel/network connectivity
   - ACS cannot reach your tunnel
   
4. **If you see connection attempt but it fails:**
   - Issue is with the WebSocket handler
   - Check for errors in agent service initialization

## Testing the Full Flow

1. **Terminal 1 - Backend:**
   ```bash
   cd api
   python main.py
   ```

2. **Terminal 2 - Dev Tunnel:**
   ```bash
   devtunnel host
   ```
   
   Copy the public URL

3. **Update `.env` with tunnel URL**

4. **Terminal 3 - Test WebSocket:**
   ```bash
   python test_websocket.py
   ```

5. **Make a call from UI**

6. **Check logs for:**
   - ✅ WebSocket URL logged
   - ✅ Call created successfully
   - ✅ WebSocket connection attempt
   - ✅ Agent/Voice service started

## Still Having Issues?

Check these environment variables in your `.env`:

```bash
# Required
CALLBACK_URI_HOST=https://your-tunnel-url
AZURE_VOICE_LIVE_ENDPOINT=https://...
AI_FOUNDRY_AGENT_ID=...
AI_FOUNDRY_PROJECT_NAME=...
AGENT_PHONE_NUMBER=+1...
TARGET_CANDIDATE_PHONE_NUMBER=+1...

# Optional but recommended
COSMOS_DB_URL=...  # For transcript storage
REDIS_URL=...      # For session caching
```

## Quick Fix Checklist

- [ ] Dev tunnel running with `--protocol auto`
- [ ] Backend server running on port 8000
- [ ] `.env` has correct CALLBACK_URI_HOST (https, not http)
- [ ] WebSocket URL shows in logs
- [ ] test_websocket.py succeeds
- [ ] Phone numbers in correct format (+1...)
- [ ] Agent credentials valid

