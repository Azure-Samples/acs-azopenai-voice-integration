import { products } from '../data/products';

const ProductDetails = ({ productId, storageOption = null }) => {
  const product = products[productId];

  if (!product) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Product not found.</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 my-2">
      <div className="flex items-center mb-3">
        <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
          <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
        </svg>
        <h4 className="font-semibold text-blue-900">Product Details</h4>
      </div>

      <div className="bg-white rounded-lg p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <img
            src={product.image}
            alt={product.name}
            className="w-full md:w-48 h-48 object-cover rounded-lg"
          />
          
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 mb-1">{product.name}</h3>
            <p className="text-sm text-gray-600 mb-3">{product.brand}</p>
            
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Features:</h4>
              <ul className="space-y-1">
                {product.features.map((feature, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-center">
                    <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Available Storage Options:</h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(product.storageOptions).map(([storage, details]) => (
                  <div
                    key={storage}
                    className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center"
                  >
                    <div className="font-semibold text-sm">{storage}</div>
                    <div className="text-blue-600 font-bold mt-1">{details.displayPrice}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="text-center text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded p-2">
              💬 Ask me about any storage option or if you'd like to choose this device!
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetails;

