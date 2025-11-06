import { plans } from '../data/products';

const PlanOptions = ({ productId, contractLength = "24" }) => {
  const contractOptions = ["12", "24", "36"];

  return (
    <div className="bg-gradient-to-r from-green-50 to-teal-50 border border-green-200 rounded-lg p-4 my-2">
      <div className="flex items-center mb-3">
        <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
          <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
        </svg>
        <h4 className="font-semibold text-green-900">Choose Your Plan</h4>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">Available Contract Lengths:</p>
        <div className="flex gap-2">
          {contractOptions.map((months) => (
            <div
              key={months}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700"
            >
              {months} months
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        {Object.values(plans).map((plan) => (
          <div
            key={plan.id}
            className="border-2 border-gray-200 bg-white rounded-lg p-4 shadow-sm"
          >
            <div className="flex justify-between items-start mb-2">
              <h5 className="font-bold text-lg">{plan.name}</h5>
              <div className="text-right">
                <p className="text-xl font-bold text-green-600">{plan.displayPrice}</p>
                <p className="text-xs text-gray-500">per month</p>
              </div>
            </div>
            
            <p className="text-sm font-semibold text-gray-700 mb-2">{plan.data} Data</p>
            
            <ul className="space-y-1">
              {plan.features.map((feature, idx) => (
                <li key={idx} className="text-xs text-gray-600 flex items-start">
                  <svg className="w-3 h-3 text-green-500 mr-1.5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="text-center text-sm text-gray-600 bg-green-50 border border-green-200 rounded p-2">
        💬 Ask me about any plan or tell me which contract length you prefer!
      </div>
    </div>
  );
};

export default PlanOptions;

