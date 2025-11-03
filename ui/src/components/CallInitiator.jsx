import { useState, useEffect } from 'react';
import { initiateOutboundCall, fetchPersonas } from '../services/api';

const CallInitiator = ({ onCallInitiated }) => {
  const [formData, setFormData] = useState({
    phone_number: '',
    candidate_name: '',
    use_agent: true,
    persona: 'default',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [personas, setPersonas] = useState([{ value: 'default', label: 'Default' }]);
  const [personasLoading, setPersonasLoading] = useState(true);

  // Fetch available personas on component mount
  useEffect(() => {
    const loadPersonas = async () => {
      setPersonasLoading(true);
      const result = await fetchPersonas();
      if (result.success && result.data) {
        setPersonas(result.data);
      }
      setPersonasLoading(false);
    };
    
    loadPersonas();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    // Validate phone number
    if (!formData.phone_number.match(/^\+?[1-9]\d{1,14}$/)) {
      setError('Please enter a valid phone number with country code (e.g., +1234567890)');
      setLoading(false);
      return;
    }

    const result = await initiateOutboundCall(formData);

    if (result.success) {
      setSuccess(true);
      setError(null);
      if (onCallInitiated) {
        // Pass the call connection ID to parent component
        onCallInitiated({
          ...formData,
          callConnectionId: result.callConnectionId,
          sessionId: result.sessionId,
        });
      }
      // Reset form after 2 seconds
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } else {
      setError(result.error);
      setSuccess(false);
    }

    setLoading(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Initiate Outbound Call</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number *
          </label>
          <input
            type="tel"
            id="phone_number"
            name="phone_number"
            value={formData.phone_number}
            onChange={handleChange}
            placeholder="+1234567890"
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500">Include country code (e.g., +1 for US)</p>
        </div>

        <div>
          <label htmlFor="candidate_name" className="block text-sm font-medium text-gray-700 mb-2">
            Candidate Name
          </label>
          <input
            type="text"
            id="candidate_name"
            name="candidate_name"
            value={formData.candidate_name}
            onChange={handleChange}
            placeholder="John Doe"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label htmlFor="persona" className="block text-sm font-medium text-gray-700 mb-2">
            AI Persona
          </label>
          <select
            id="persona"
            name="persona"
            value={formData.persona}
            onChange={handleChange}
            disabled={personasLoading}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {personasLoading ? (
              <option value="">Loading personas...</option>
            ) : (
              personas.map((persona) => (
                <option key={persona.value} value={persona.value}>
                  {persona.label}
                </option>
              ))
            )}
          </select>
          {personas.length === 0 && !personasLoading && (
            <p className="mt-1 text-xs text-red-500">Failed to load personas. Using default.</p>
          )}
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="use_agent"
            name="use_agent"
            checked={formData.use_agent}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="use_agent" className="ml-2 block text-sm text-gray-700">
            Use AI Foundry Agent Mode
          </label>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">✓ Call initiated successfully!</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 px-4 rounded-md font-semibold text-white transition-colors ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Initiating Call...
            </span>
          ) : (
            'Initiate Call'
          )}
        </button>
      </form>
    </div>
  );
};

export default CallInitiator;

