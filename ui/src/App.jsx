import { useState } from 'react';
import CallInitiator from './components/CallInitiator';
import TranscriptViewer from './components/TranscriptViewer';

function App() {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);
  const [currentCallInfo, setCurrentCallInfo] = useState(null);

  const handleCallInitiated = (callData) => {
    console.log('Call initiated:', callData);
    
    // Automatically set the current session ID from the API response
    if (callData.callConnectionId) {
      setCurrentSessionId(callData.callConnectionId);
      setCurrentCallInfo({
        phoneNumber: callData.phone_number,
        name: callData.candidate_name,
        callConnectionId: callData.callConnectionId,
      });
    }
    
    // Add to session history
    const newSession = {
      id: callData.callConnectionId || Date.now(),
      phoneNumber: callData.phone_number,
      name: callData.candidate_name,
      timestamp: new Date().toISOString(),
      useAgent: callData.use_agent,
      callConnectionId: callData.callConnectionId,
    };
    setSessionHistory([newSession, ...sessionHistory]);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                ACS Voice Integration Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                Azure Communication Services + OpenAI Voice Live
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                <span className="w-2 h-2 bg-blue-600 rounded-full mr-2"></span>
                Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Call Initiator */}
          <div className="space-y-6">
            <CallInitiator onCallInitiated={handleCallInitiated} />
            
            {/* Active Call Info */}
            {currentCallInfo && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Active Call
                  </h3>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <span className="animate-pulse mr-2">●</span>
                    Live
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Phone:</span>
                    <span className="font-medium">{currentCallInfo.phoneNumber}</span>
                  </div>
                  {currentCallInfo.name && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Name:</span>
                      <span className="font-medium">{currentCallInfo.name}</span>
                    </div>
                  )}
                  <div className="mt-3 p-2 bg-gray-50 rounded">
                    <p className="text-xs text-gray-600 mb-1">Session ID:</p>
                    <p className="font-mono text-xs break-all">{currentCallInfo.callConnectionId}</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setCurrentSessionId(null);
                    setCurrentCallInfo(null);
                  }}
                  className="mt-4 w-full px-4 py-2 text-sm text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition-colors"
                >
                  Stop Monitoring
                </button>
              </div>
            )}
            
            {/* Manual Session ID Input (Optional) */}
            {!currentCallInfo && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  Monitor Existing Session
                </h3>
                <div className="space-y-3">
                  <div>
                    <label htmlFor="session_id" className="block text-sm font-medium text-gray-700 mb-2">
                      Enter Call Connection ID
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        id="session_id"
                        placeholder="e.g., aHR0cHM6Ly9..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && e.target.value) {
                            setCurrentSessionId(e.target.value);
                            setCurrentCallInfo({
                              phoneNumber: 'Unknown',
                              callConnectionId: e.target.value,
                            });
                          }
                        }}
                      />
                      <button
                        onClick={(e) => {
                          const input = document.getElementById('session_id');
                          if (input.value) {
                            setCurrentSessionId(input.value);
                            setCurrentCallInfo({
                              phoneNumber: 'Unknown',
                              callConnectionId: input.value,
                            });
                          }
                        }}
                        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      >
                        Load
                      </button>
                    </div>
                    <p className="mt-2 text-xs text-gray-500">
                      Load an existing session from Cosmos DB
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Recent Sessions */}
            {sessionHistory.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  Recent Calls
                </h3>
                <div className="space-y-2">
                  {sessionHistory.slice(0, 5).map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => {
                        if (session.callConnectionId) {
                          setCurrentSessionId(session.callConnectionId);
                          setCurrentCallInfo({
                            phoneNumber: session.phoneNumber,
                            name: session.name,
                            callConnectionId: session.callConnectionId,
                          });
                        }
                      }}
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {session.name || session.phoneNumber}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(session.timestamp).toLocaleTimeString()} • {session.useAgent ? 'Agent' : 'Non-Agent'}
                        </p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                        View
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Transcript Viewer */}
          <div className="lg:sticky lg:top-8 self-start">
            <TranscriptViewer sessionId={currentSessionId} autoRefresh={true} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            ACS Voice Integration Dashboard • Built with React + Vite + TailwindCSS
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

