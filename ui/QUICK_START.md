# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   cd ui
   npm install
   ```

2. **Start the UI:**
   ```bash
   npm run dev
   ```

3. **Open browser:**
   ```
   http://localhost:3000
   ```

## Making Your First Call

1. **In the UI:**
   - Enter phone number: `+1234567890`
   - Click "Initiate Call"

2. **Get the Call Connection ID:**
   
   From your backend logs, look for:
   ```
   Created call with connection id: aHR0cHM6Ly9...
   ```

3. **Monitor the Transcript:**
   - Copy the Call Connection ID
   - Paste it into "Enter ACS Call Connection ID" field
   - Click "Load"
   - Watch the conversation appear in real-time! 🎉

## Architecture Flow

```
User → UI (React) → Backend API (Python/Quart)
                         ↓
                    Azure ACS Call
                         ↓
                    Voice Live API
                         ↓
                    Cosmos DB (Transcripts)
                         ↓
                    UI (Real-time Display)
```

## Key Files

- `src/App.jsx` - Main dashboard layout
- `src/components/CallInitiator.jsx` - Call form
- `src/components/TranscriptViewer.jsx` - Live transcript
- `src/services/api.js` - Backend communication

## Environment Variables

Create a `.env` file if backend runs on different port:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Common Session IDs Format

ACS Call Connection IDs typically look like:
```
aHR0cHM6Ly9jb252LXVzd2UtMDEuY29udi5za3lwZS5jb20vY29udi8...
```

## Tips

- ✅ Ensure backend API is running first
- ✅ Check Cosmos DB is configured and accessible
- ✅ Verify phone number includes country code
- ✅ Use Chrome/Firefox for best experience
- ✅ Open browser console to debug API issues

## Troubleshooting

**"Network Error" when initiating call:**
- Check backend is running on port 8000
- Verify CORS settings allow localhost:3000

**"Session not found" when loading transcript:**
- Ensure Call Connection ID is correct and complete
- Check that call was successfully created
- Verify Cosmos DB has the session record

**Transcript not updating:**
- Confirm call is active
- Check browser console for errors
- Verify auto-refresh is enabled

Happy calling! 📞✨

