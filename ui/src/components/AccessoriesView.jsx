import { getAccessoriesFor } from '../data/products';

const AccessoriesView = ({ productId }) => {
  const accessories = getAccessoriesFor(productId);

  if (accessories.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-600">No accessories available for this product.</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-4 my-2">
      <div className="flex items-center mb-3">
        <svg className="w-5 h-5 text-indigo-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 2a4 4 0 00-4 4v1H5a1 1 0 00-.994.89l-1 9A1 1 0 004 18h12a1 1 0 00.994-1.11l-1-9A1 1 0 0015 7h-1V6a4 4 0 00-4-4zm2 5V6a2 2 0 10-4 0v1h4zm-6 3a1 1 0 112 0 1 1 0 01-2 0zm7-1a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
        </svg>
        <h4 className="font-semibold text-indigo-900">Perfect Additions</h4>
      </div>

      <p className="text-sm text-gray-700 mb-4">
        Enhance your experience with these recommended accessories:
      </p>

      <div className="space-y-3 mb-4">
        {accessories.map((accessory) => {
          const price = Object.values(accessory.storageOptions)[0];

          return (
            <div
              key={accessory.id}
              className="border-2 border-gray-200 bg-white rounded-lg p-3 shadow-sm"
            >
              <div className="flex gap-3">
                <img
                  src={accessory.image}
                  alt={accessory.name}
                  className="w-16 h-16 object-cover rounded"
                />
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h5 className="font-semibold text-sm">{accessory.name}</h5>
                      <p className="text-xs text-gray-600 mt-0.5">{accessory.subcategory}</p>
                    </div>
                    <span className="font-bold text-indigo-600">{price.displayPrice}</span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {accessory.features.slice(0, 2).map((feature, idx) => (
                      <span key={idx} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-center text-sm text-gray-600 bg-indigo-50 border border-indigo-200 rounded p-2">
        💬 Let me know which accessories interest you, or if you'd like to skip this step!
      </div>
    </div>
  );
};

export default AccessoriesView;

