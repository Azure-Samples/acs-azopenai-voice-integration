import { products, filterProducts } from '../data/products';

const ProductCarousel = ({ category, filter = "all", maxPrice = null }) => {
  const filteredProducts = filterProducts(category, filter, maxPrice);

  if (filteredProducts.length === 0) {
    return (
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <p className="text-gray-600">No products found matching your criteria.</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 my-2">
      <div className="flex items-center mb-3">
        <svg className="w-5 h-5 text-purple-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
        </svg>
        <h4 className="font-semibold text-purple-900">
          Browse {category === 'phones' ? 'Phones' : 'Tablets'}
          {filter !== 'all' && ` - ${filter.replace('-', ' ')}`}
        </h4>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filteredProducts.map((product) => (
          <div
            key={product.id}
            className="border-2 border-gray-200 bg-white rounded-lg p-3 shadow-sm"
          >
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-32 object-cover rounded mb-2"
            />
            <h5 className="font-semibold text-sm mb-1">{product.name}</h5>
            <p className="text-xs text-gray-600 mb-2">From {Object.values(product.storageOptions)[0].displayPrice}</p>
            <div className="mb-2">
              <p className="text-xs text-gray-500 mb-1">Storage options:</p>
              <div className="flex flex-wrap gap-1">
                {Object.entries(product.storageOptions).map(([storage, details]) => (
                  <span key={storage} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                    {storage}: {details.displayPrice}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-1">
              {product.features.slice(0, 3).map((feature, idx) => (
                <span key={idx} className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                  {feature}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-3 text-center text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded p-2">
        💬 Ask me about any product for more details, or tell me which one interests you!
      </div>
    </div>
  );
};

export default ProductCarousel;

