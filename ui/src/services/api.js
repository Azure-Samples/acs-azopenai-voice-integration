import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const initiateOutboundCall = async (callData) => {
  try {
    const response = await api.post('/api/initiateOutboundCall', callData);
    // Backend now returns { success, call_connection_id, session_id, message }
    return { 
      success: true, 
      data: response.data,
      callConnectionId: response.data.call_connection_id,
      sessionId: response.data.session_id
    };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.details || error.message || 'Failed to initiate call',
    };
  }
};

export const fetchTranscript = async (sessionId) => {
  try {
    const response = await api.get(`/api/transcript/${sessionId}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.details || error.message || 'Failed to fetch transcript',
    };
  }
};

export const fetchActiveSessions = async () => {
  try {
    const response = await api.get('/api/sessions/active');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.details || error.message || 'Failed to fetch sessions',
    };
  }
};

export const fetchPersonas = async () => {
  try {
    const response = await api.get('/api/personas');
    return { success: true, data: response.data.personas };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.details || error.message || 'Failed to fetch personas',
      data: [{ value: 'default', label: 'Default' }] // Fallback
    };
  }
};

export default api;

