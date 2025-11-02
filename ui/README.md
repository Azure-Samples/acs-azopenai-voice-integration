# ACS Voice Integration Dashboard

A modern React-based UI for managing Azure Communication Services (ACS) outbound calls with OpenAI Voice Live integration. This dashboard allows you to initiate calls and monitor real-time transcripts of conversations between users and AI agents.

## Features

- 🚀 **Initiate Outbound Calls** - Trigger calls with customizable parameters
- 💬 **Real-Time Transcripts** - View live conversation transcripts as they happen
- 🤖 **Agent Mode Support** - Toggle between AI Foundry Agent and non-agent modes
- 🎨 **Modern UI** - Built with React, Vite, and TailwindCSS
- 📊 **Session Management** - Track and monitor active call sessions
- ⚡ **Auto-Refresh** - Transcripts update automatically every 2 seconds

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000` (or configure different URL)
- Cosmos DB configured in the backend for transcript storage

## Installation

1. **Navigate to the UI directory:**
   ```bash
   cd ui
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure API endpoint (optional):**
   
   If your backend runs on a different URL, create a `.env` file:
   ```bash
   VITE_API_BASE_URL=http://your-backend-url:port
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   
   Navigate to `http://localhost:3000`

## Usage

### Initiating a Call

1. Fill in the call parameters:
   - **Phone Number** (required): Include country code (e.g., +1234567890)
   - **Candidate Name** (optional): Name of the person being called
   - **AI Persona**: Select the AI personality for the call
   - **Use AI Foundry Agent Mode**: Toggle agent mode on/off

2. Click **Initiate Call** button

3. The call will be created and you'll receive a success notification

### Viewing Transcripts

1. **Get the Session ID:**
   - The session ID is the ACS Call Connection ID
   - You can find it in:
     - Backend API logs
     - Cosmos DB database
     - Azure portal (ACS resource)

2. **Enter Session ID:**
   - Paste the Call Connection ID in the "Monitor Session" input field
   - Click **Load** or press Enter

3. **Watch Live Transcript:**
   - The transcript will auto-refresh every 2 seconds
   - User messages appear on the right (blue)
   - AI Agent messages appear on the left (gray)
   - Call status indicator shows Live/Ended

## Project Structure

```
ui/
├── src/
│   ├── components/
│   │   ├── CallInitiator.jsx      # Form to initiate calls
│   │   └── TranscriptViewer.jsx   # Real-time transcript display
│   ├── services/
│   │   └── api.js                 # API service layer
│   ├── App.jsx                    # Main application component
│   ├── main.jsx                   # React entry point
│   └── index.css                  # Global styles with Tailwind
├── public/                        # Static assets
├── index.html                     # HTML template
├── package.json                   # Dependencies
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind CSS config
└── postcss.config.js              # PostCSS config
```

## API Endpoints Used

The UI interacts with the following backend endpoints:

- `POST /api/initiateOutboundCall` - Start a new outbound call
- `GET /api/transcript/<session_id>` - Fetch transcript for a session

## Development

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

### Proxy Configuration

The Vite dev server is configured to proxy API requests to `http://localhost:8000`. This is defined in `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## Customization

### Changing AI Personas

Edit the persona options in `src/components/CallInitiator.jsx`:

```javascript
<option value="default">Default</option>
<option value="joyce">Joyce</option>
<option value="recruiter">Recruiter</option>
<option value="customer_service">Customer Service</option>
```

### Adjusting Auto-Refresh Rate

Modify the interval in `src/components/TranscriptViewer.jsx`:

```javascript
// Change 2000ms (2 seconds) to your preferred interval
intervalId = setInterval(loadTranscript, 2000);
```

### Styling

The UI uses TailwindCSS for styling. Customize colors and themes in `tailwind.config.js` or modify component classes directly.

## Troubleshooting

### "Cosmos DB not configured" Error

- Ensure your backend has Cosmos DB properly configured
- Check that `COSMOS_DB_URL` is set in backend environment variables

### "Session not found" Error

- Verify the Call Connection ID is correct
- Check that the call was successfully created in Cosmos DB
- Ensure the session ID format matches what's stored in the database

### Transcript Not Updating

- Confirm the call is active and conversation is happening
- Check browser console for API errors
- Verify backend is storing transcripts (check logs)
- Ensure Cosmos DB is accessible from the backend

### API Connection Issues

- Verify backend API is running on the expected URL
- Check CORS settings if running on different domains
- Review browser network tab for failed requests

## Technologies Used

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Axios** - HTTP client for API requests

## Contributing

When adding new features:

1. Create new components in `src/components/`
2. Add API methods to `src/services/api.js`
3. Update this README with new functionality

## License

This project is part of the ACS Voice Integration solution.

## Support

For issues or questions:
- Check backend API logs
- Review Azure Communication Services documentation
- Verify Cosmos DB connection and data structure

