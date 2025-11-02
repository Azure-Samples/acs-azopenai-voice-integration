import { useState, useEffect, useRef } from 'react';
import { fetchTranscript } from '../services/api';

const TranscriptViewer = ({ sessionId, autoRefresh = true }) => {
  const [transcript, setTranscript] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const [error, setError] = useState(null);
  const [sessionInfo, setSessionInfo] = useState(null);
  const transcriptEndRef = useRef(null);

  const scrollToBottom = () => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [transcript]);

  useEffect(() => {
    if (!sessionId) return;

    const loadTranscript = async (isInitial = false) => {
      // Only show loading on initial load, not on refresh
      if (isInitial) {
        setLoading(true);
      }
      
      const result = await fetchTranscript(sessionId);
      
      if (result.success) {
        const conversation = result.data.conversation || [];
        console.log('Transcript data:', conversation); // Debug log
        setTranscript(conversation);
        setSessionInfo({
          callerId: result.data.callerId,
          callStartTime: result.data.callStartTime,
          callEndTime: result.data.callEndTime,
        });
        
        // Check if Cosmos DB returned an error message
        if (result.data.error) {
          setError(`⚠️ ${result.data.error}`);
        } else {
          setError(null);
        }
      } else {
        setError(result.error);
      }
      
      if (isInitial) {
        setLoading(false);
        setInitialLoad(false);
      }
    };

    // Initial load
    loadTranscript(true);

    // Auto-refresh every 2 seconds if enabled and call is active
    let intervalId;
    if (autoRefresh) {
      intervalId = setInterval(() => loadTranscript(false), 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [sessionId, autoRefresh]);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  const getMessageBubbleClass = (sender) => {
    const baseClasses = "max-w-[70%] rounded-lg p-4 mb-4 shadow-sm";
    
    if (sender === 'user') {
      return `${baseClasses} bg-blue-100 ml-auto text-right`;
    } else if (sender === 'agent' || sender === 'assistant') {
      return `${baseClasses} bg-gray-100 mr-auto`;
    }
    return `${baseClasses} bg-yellow-50 mx-auto`;
  };

  const getSenderLabel = (sender) => {
    if (sender === 'user') return '👤 User';
    if (sender === 'agent') return '🤖 AI Agent';
    if (sender === 'assistant') return '🤖 AI Assistant';
    return sender;
  };
  
  const getSenderIcon = (sender) => {
    if (sender === 'user') {
      return (
        <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
        <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" />
        <path d="M6 9a2 2 0 114 0 2 2 0 01-4 0zM10 9a2 2 0 114 0 2 2 0 01-4 0z" />
      </svg>
    );
  };

  if (!sessionId) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Live Transcript</h2>
        <div className="text-center py-12 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p className="text-lg">No active session</p>
          <p className="text-sm mt-2">Initiate a call to see the transcript here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 flex flex-col h-full">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800">Live Transcript</h2>
          {sessionInfo?.callEndTime ? (
            <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
              Call Ended
            </span>
          ) : (
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium flex items-center">
              <span className="animate-pulse mr-2">●</span>
              Live
            </span>
          )}
        </div>
        {sessionInfo && (
          <div className="mt-2 text-sm text-gray-600 space-y-1">
            <p>Session ID: <span className="font-mono text-xs">{sessionId}</span></p>
            {sessionInfo.callerId && <p>Caller: {sessionInfo.callerId}</p>}
            {sessionInfo.callStartTime && (
              <p>Started: {formatTimestamp(sessionInfo.callStartTime)}</p>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg p-4 min-h-[400px] max-h-[600px]">
        {loading && transcript.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-gray-600">Loading transcript...</p>
            </div>
          </div>
        ) : transcript.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Waiting for conversation to start...</p>
          </div>
        ) : (
          <div className="space-y-2">
            {transcript.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={getMessageBubbleClass(message.sender)}>
                  <div className="flex items-center mb-2">
                    {getSenderIcon(message.sender)}
                    <span className="font-semibold text-sm text-gray-700 flex-1">
                      {getSenderLabel(message.sender)}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{message.message}</p>
                </div>
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>
        )}
      </div>

      {transcript.length > 0 && (
        <div className="mt-4 text-sm text-gray-500 text-center">
          {transcript.length} message{transcript.length !== 1 ? 's' : ''} in conversation
        </div>
      )}
    </div>
  );
};

export default TranscriptViewer;

