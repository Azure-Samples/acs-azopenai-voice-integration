// Vodafone product catalog
export const products = {
  "iphone-15-pro": {
    id: "iphone-15-pro",
    name: "iPhone 15 Pro",
    brand: "Apple",
    category: "phones",
    image: "https://images.unsplash.com/photo-1696446702884-cbd2c85cd5ea?w=400",
    basePrice: 999,
    storageOptions: {
      "128GB": { price: 999, displayPrice: "£999" },
      "256GB": { price: 1199, displayPrice: "£1,199" },
      "512GB": { price: 1399, displayPrice: "£1,399" },
      "1TB": { price: 1499, displayPrice: "£1,499" }
    },
    features: ["A17 Pro chip", "Titanium design", "48MP camera", "Action button"],
    tags: ["premium", "camera-focused"]
  },
  "iphone-15": {
    id: "iphone-15",
    name: "iPhone 15",
    brand: "Apple",
    category: "phones",
    image: "https://images.unsplash.com/photo-1695048133139-34d67da5a98a?w=400",
    basePrice: 799,
    storageOptions: {
      "128GB": { price: 799, displayPrice: "£799" },
      "256GB": { price: 949, displayPrice: "£949" },
      "512GB": { price: 1099, displayPrice: "£1,099" }
    },
    features: ["Dynamic Island", "Great battery life", "48MP camera", "USB-C"],
    tags: ["all", "camera-focused"]
  },
  "samsung-s24-ultra": {
    id: "samsung-s24-ultra",
    name: "Samsung Galaxy S24 Ultra",
    brand: "Samsung",
    category: "phones",
    image: "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400",
    basePrice: 1149,
    storageOptions: {
      "256GB": { price: 1149, displayPrice: "£1,149" },
      "512GB": { price: 1299, displayPrice: "£1,299" },
      "1TB": { price: 1449, displayPrice: "£1,449" }
    },
    features: ["S Pen included", "AI photo editing", "200MP camera", "Titanium frame"],
    tags: ["premium", "camera-focused"]
  },
  "samsung-s24": {
    id: "samsung-s24",
    name: "Samsung Galaxy S24",
    brand: "Samsung",
    category: "phones",
    image: "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400",
    basePrice: 799,
    storageOptions: {
      "128GB": { price: 799, displayPrice: "£799" },
      "256GB": { price: 949, displayPrice: "£949" }
    },
    features: ["Compact design", "Powerful performance", "50MP camera", "AI features"],
    tags: ["all"]
  },
  "pixel-8-pro": {
    id: "pixel-8-pro",
    name: "Google Pixel 8 Pro",
    brand: "Google",
    category: "phones",
    image: "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400",
    basePrice: 899,
    storageOptions: {
      "128GB": { price: 899, displayPrice: "£899" },
      "256GB": { price: 1019, displayPrice: "£1,019" },
      "512GB": { price: 1179, displayPrice: "£1,179" }
    },
    features: ["Best Android camera", "Pure Google experience", "AI features", "7 years updates"],
    tags: ["premium", "camera-focused"]
  },
  "ipad-pro-11": {
    id: "ipad-pro-11",
    name: "iPad Pro 11\"",
    brand: "Apple",
    category: "tablets",
    image: "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400",
    basePrice: 799,
    storageOptions: {
      "128GB": { price: 799, displayPrice: "£799" },
      "256GB": { price: 999, displayPrice: "£999" },
      "512GB": { price: 1399, displayPrice: "£1,399" },
      "1TB": { price: 1799, displayPrice: "£1,799" },
      "2TB": { price: 2199, displayPrice: "£2,199" }
    },
    features: ["M2 chip", "Liquid Retina display", "ProMotion 120Hz", "Apple Pencil support"],
    tags: ["premium"]
  },
  "ipad-air": {
    id: "ipad-air",
    name: "iPad Air",
    brand: "Apple",
    category: "tablets",
    image: "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=400",
    basePrice: 569,
    storageOptions: {
      "64GB": { price: 569, displayPrice: "£569" },
      "256GB": { price: 729, displayPrice: "£729" }
    },
    features: ["M1 chip", "Great value", "Apple Pencil support", "All-day battery"],
    tags: ["all", "budget"]
  },
  "galaxy-tab-s9": {
    id: "galaxy-tab-s9",
    name: "Samsung Galaxy Tab S9",
    brand: "Samsung",
    category: "tablets",
    image: "https://images.unsplash.com/photo-1585790050230-5dd28404f869?w=400",
    basePrice: 699,
    storageOptions: {
      "128GB": { price: 699, displayPrice: "£699" },
      "256GB": { price: 849, displayPrice: "£849" }
    },
    features: ["AMOLED display", "S Pen included", "DeX mode", "IP68 water resistant"],
    tags: ["all"]
  },
  "airpods-pro-2": {
    id: "airpods-pro-2",
    name: "Apple AirPods Pro (2nd Gen)",
    brand: "Apple",
    category: "accessories",
    subcategory: "earphones",
    image: "https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=400",
    basePrice: 229,
    storageOptions: {
      "Standard": { price: 229, displayPrice: "£229" }
    },
    features: ["Active Noise Cancellation", "Transparency mode", "Spatial audio", "32hr battery"],
    tags: ["premium"],
    compatibleWith: ["iphone-15-pro", "iphone-15"]
  },
  "samsung-buds-2-pro": {
    id: "samsung-buds-2-pro",
    name: "Samsung Galaxy Buds 2 Pro",
    brand: "Samsung",
    category: "accessories",
    subcategory: "earphones",
    image: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400",
    basePrice: 179,
    storageOptions: {
      "Standard": { price: 179, displayPrice: "£179" }
    },
    features: ["ANC", "360 Audio", "IPX7 water resistant", "18hr battery"],
    tags: ["premium"],
    compatibleWith: ["samsung-s24-ultra", "samsung-s24"]
  },
  "phone-case-premium": {
    id: "phone-case-premium",
    name: "Premium Protective Case",
    brand: "Vodafone",
    category: "accessories",
    subcategory: "cases",
    image: "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400",
    basePrice: 29,
    storageOptions: {
      "Standard": { price: 29, displayPrice: "£29" }
    },
    features: ["Military-grade protection", "Wireless charging compatible", "Slim design"],
    tags: ["all"],
    compatibleWith: ["iphone-15-pro", "iphone-15", "samsung-s24-ultra", "samsung-s24", "pixel-8-pro"]
  },
  "screen-protector": {
    id: "screen-protector",
    name: "Tempered Glass Screen Protector",
    brand: "Vodafone",
    category: "accessories",
    subcategory: "screen-protection",
    image: "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400",
    basePrice: 15,
    storageOptions: {
      "Standard": { price: 15, displayPrice: "£15" }
    },
    features: ["9H hardness", "Bubble-free application", "2-pack"],
    tags: ["all"],
    compatibleWith: ["iphone-15-pro", "iphone-15", "samsung-s24-ultra", "samsung-s24", "pixel-8-pro"]
  },
  "wireless-charger": {
    id: "wireless-charger",
    name: "Fast Wireless Charger",
    brand: "Vodafone",
    category: "accessories",
    subcategory: "chargers",
    image: "https://images.unsplash.com/photo-1591290619762-d11ba6f42e42?w=400",
    basePrice: 39,
    storageOptions: {
      "Standard": { price: 39, displayPrice: "£39" }
    },
    features: ["15W fast charging", "LED indicator", "Universal compatibility"],
    tags: ["all"],
    compatibleWith: ["iphone-15-pro", "iphone-15", "samsung-s24-ultra", "samsung-s24", "pixel-8-pro"]
  }
};

export const plans = {
  "essentials": {
    id: "essentials",
    name: "Essentials",
    data: "5GB",
    price: 11,
    displayPrice: "£11/month",
    features: ["5GB data", "Unlimited calls & texts", "EU roaming"]
  },
  "standard": {
    id: "standard",
    name: "Standard",
    data: "20GB",
    price: 15,
    displayPrice: "£15/month",
    features: ["20GB data", "Unlimited calls & texts", "EU roaming", "Social media pass"]
  },
  "premium": {
    id: "premium",
    name: "Premium",
    data: "100GB",
    price: 25,
    displayPrice: "£25/month",
    features: ["100GB data", "Unlimited calls & texts", "Global roaming", "Unlimited social media", "Streaming pass"]
  },
  "unlimited": {
    id: "unlimited",
    name: "Unlimited Max",
    data: "Unlimited",
    price: 35,
    displayPrice: "£35/month",
    features: ["Truly unlimited 5G data", "Unlimited calls & texts", "Global roaming", "Unlimited everything", "Premium streaming"]
  }
};

export function filterProducts(category, filter = "all", maxPrice = null) {
  let filtered = Object.values(products).filter(p => p.category === category);
  
  if (filter !== "all") {
    filtered = filtered.filter(p => p.tags.includes(filter));
  }
  
  if (maxPrice) {
    filtered = filtered.filter(p => p.basePrice <= maxPrice);
  }
  
  return filtered;
}

export function getAccessoriesFor(productId) {
  return Object.values(products).filter(p => 
    p.category === "accessories" && 
    p.compatibleWith && 
    p.compatibleWith.includes(productId)
  );
}

