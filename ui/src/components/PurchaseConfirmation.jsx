import { products, plans } from '../data/products';

const PurchaseConfirmation = ({ purchaseDetails }) => {
  const { product_id, storage, plan_id, contract_length } = purchaseDetails;
  
  const product = products[product_id];
  const plan = plan_id ? plans[plan_id] : null;

  if (!product) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Product not found.</p>
      </div>
    );
  }

  const productPrice = storage ? product.storageOptions[storage]?.price : product.basePrice;
  const monthlyDeviceCost = contract_length ? (productPrice / parseInt(contract_length)).toFixed(2) : 0;
  const totalMonthlyCost = plan ? (parseFloat(monthlyDeviceCost) + plan.price).toFixed(2) : monthlyDeviceCost;

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-300 rounded-lg p-4 my-2">
      <div className="flex items-center mb-3">
        <svg className="w-6 h-6 text-amber-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
          <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
        </svg>
        <h4 className="font-bold text-amber-900 text-lg">Purchase Summary</h4>
      </div>

      <div className="bg-white rounded-lg p-4 mb-4">
        <div className="flex gap-4 mb-4">
          <img src={product.image} alt={product.name} className="w-24 h-24 object-cover rounded" />
          <div className="flex-1">
            <h3 className="font-bold text-lg">{product.name}</h3>
            {storage && <p className="text-sm text-gray-600">{storage}</p>}
            <p className="text-2xl font-bold text-amber-600 mt-2">
              £{productPrice}
            </p>
          </div>
        </div>

        {plan && (
          <div className="border-t pt-3 mb-3">
            <h4 className="font-semibold mb-2">Monthly Plan</h4>
            <div className="flex justify-between">
              <span>{plan.name} ({plan.data})</span>
              <span className="font-semibold">{plan.displayPrice}</span>
            </div>
          </div>
        )}

        {contract_length && (
          <div className="border-t pt-3 mb-3">
            <h4 className="font-semibold mb-2">Contract Terms</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Contract length:</span>
                <span className="font-medium">{contract_length} months</span>
              </div>
              <div className="flex justify-between">
                <span>Device payment:</span>
                <span className="font-medium">£{monthlyDeviceCost}/month</span>
              </div>
              {plan && (
                <>
                  <div className="flex justify-between">
                    <span>Plan cost:</span>
                    <span className="font-medium">{plan.displayPrice}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2 mt-2 font-bold text-base">
                    <span>Total monthly cost:</span>
                    <span className="text-amber-600">£{totalMonthlyCost}/month</span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
          <p className="text-blue-800">
            <strong>What's included:</strong> Free UK delivery, 30-day money-back guarantee, 
            and 12-month manufacturer warranty.
          </p>
        </div>
      </div>

      <div className="text-center text-sm text-gray-600 bg-amber-50 border border-amber-200 rounded p-2">
        💬 Let me know if you'd like to proceed with this purchase or if you have any questions!
      </div>
    </div>
  );
};

export default PurchaseConfirmation;

