/**
 * Normalization utilities for Shopify API responses.
 * Transforms raw Shopify API data into clean, simplified structures.
 */

type PathValue = string | number | boolean | null | undefined | Record<string, unknown> | unknown[];
type RuleFunction = (source: Record<string, unknown>) => PathValue;
type MappingRule = string | RuleFunction;
type MappingRules = Record<string, MappingRule>;

/**
 * Safe dot-notation access for nested objects.
 * Returns undefined if path fails at any point.
 */
function getPath(data: Record<string, unknown> | null | undefined, path: string): PathValue {
  if (!data) {
    return undefined;
  }
  
  let current: any = data;
  const keys = path.split('.');
  
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return undefined;
    }
  }
  
  return current;
}

/**
 * Creates a clean dictionary based on mapping rules.
 * Excludes fields with null/undefined values from output.
 */
export function normalize(
  source: Record<string, unknown> | null | undefined,
  mapping: MappingRules
): Record<string, unknown> {
  if (!source) {
    return {};
  }

  const cleanData: Record<string, unknown> = {};
  
  for (const [targetKey, rule] of Object.entries(mapping)) {
    let value: PathValue;
    
    if (typeof rule === 'string') {
      value = getPath(source, rule);
    } else if (typeof rule === 'function') {
      try {
        value = rule(source);
      } catch {
        value = undefined;
      }
    } else {
      value = undefined;
    }
    
    // Only include non-null, non-undefined values
    if (value !== null && value !== undefined) {
      cleanData[targetKey] = value;
    }
  }
  
  return cleanData;
}

/**
 * Normalize an array of items using the same mapping rules.
 */
export function normalizeArray(
  items: unknown[] | null | undefined,
  mapping: MappingRules
): Record<string, unknown>[] {
  if (!Array.isArray(items)) {
    return [];
  }
  
  return items
    .map(item => normalize(item as Record<string, unknown>, mapping))
    .filter(item => Object.keys(item).length > 0);
}

// ─────────────────────────────────────────────────────────────────────────────
// Mapping Rules - Klavis-defined field names
// ─────────────────────────────────────────────────────────────────────────────

const VARIANT_RULES: MappingRules = {
  id: 'id',
  price: 'price',
  compareAtPrice: 'compare_at_price',
  sku: 'sku',
  stock: 'inventory_quantity',
  inventoryPolicy: 'inventory_policy',
  title: 'title',
  position: 'position',
  weight: 'weight',
  weightUnit: 'weight_unit',
  requiresShipping: 'requires_shipping',
  taxable: 'taxable',
};

const IMAGE_RULES: MappingRules = {
  id: 'id',
  src: 'src',
  alt: 'alt',
  width: 'width',
  height: 'height',
  position: 'position',
};

const OPTION_RULES: MappingRules = {
  id: 'id',
  name: 'name',
  position: 'position',
  values: 'values',
};

export const PRODUCT_RULES: MappingRules = {
  id: 'id',
  title: 'title',
  description: 'body_html',
  handle: 'handle',
  vendor: 'vendor',
  category: 'product_type',
  status: 'status',
  tags: 'tags',
  publishedAt: 'published_at',
  publishedScope: 'published_scope',
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  // For single-variant products, extract first variant data
  price: (src) => {
    const variants = src.variants as any[];
    return variants?.[0]?.price;
  },
  sku: (src) => {
    const variants = src.variants as any[];
    return variants?.[0]?.sku;
  },
  stock: (src) => {
    const variants = src.variants as any[];
    return variants?.[0]?.inventory_quantity;
  },
  // Include all variants for multi-variant products
  variants: (src) => {
    const variants = src.variants as any[];
    return variants ? normalizeArray(variants, VARIANT_RULES) : undefined;
  },
  // Include product options
  options: (src) => {
    const options = src.options as any[];
    return options ? normalizeArray(options, OPTION_RULES) : undefined;
  },
  // Include product images
  images: (src) => {
    const images = src.images as any[];
    return images ? normalizeArray(images, IMAGE_RULES) : undefined;
  },
  // Primary image
  image: (src) => {
    const image = src.image as Record<string, unknown>;
    return image ? normalize(image, IMAGE_RULES) : undefined;
  },
};

const ADDRESS_RULES: MappingRules = {
  address: 'address1',
  address2: 'address2',
  city: 'city',
  state: 'province',
  zip: 'zip',
  country: 'country',
  countryCode: 'country_code',
};

export const CUSTOMER_RULES: MappingRules = {
  id: 'id',
  email: 'email',
  firstName: 'first_name',
  lastName: 'last_name',
  name: (src) => {
    const first = src.first_name as string;
    const last = src.last_name as string;
    if (first && last) return `${first} ${last}`;
    return first || last;
  },
  phone: 'phone',
  ordersCount: 'orders_count',
  totalSpent: 'total_spent',
  state: 'state',
  verifiedEmail: 'verified_email',
  taxExempt: 'tax_exempt',
  tags: 'tags',
  lastOrderId: 'last_order_id',
  lastOrderName: 'last_order_name',
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  // Flatten default address
  address: (src) => {
    const addr = src.default_address as Record<string, unknown>;
    return addr ? getPath(addr, 'address1') : undefined;
  },
  city: (src) => {
    const addr = src.default_address as Record<string, unknown>;
    return addr ? getPath(addr, 'city') : undefined;
  },
  province: (src) => {
    const addr = src.default_address as Record<string, unknown>;
    return addr ? getPath(addr, 'province') : undefined;
  },
  zip: (src) => {
    const addr = src.default_address as Record<string, unknown>;
    return addr ? getPath(addr, 'zip') : undefined;
  },
  country: (src) => {
    const addr = src.default_address as Record<string, unknown>;
    return addr ? getPath(addr, 'country') : undefined;
  },
  // Include full address object if needed
  defaultAddress: (src) => {
    const addr = src.default_address as Record<string, unknown>;
    return addr ? normalize(addr, ADDRESS_RULES) : undefined;
  },
  // Include all addresses
  addresses: (src) => {
    const addresses = src.addresses as any[];
    return addresses ? normalizeArray(addresses, ADDRESS_RULES) : undefined;
  },
};

const LINE_ITEM_RULES: MappingRules = {
  id: 'id',
  productId: 'product_id',
  variantId: 'variant_id',
  title: 'title',
  quantity: 'quantity',
  price: 'price',
  sku: 'sku',
  totalDiscount: 'total_discount',
};

const CUSTOMER_INFO_RULES: MappingRules = {
  id: 'id',
  email: 'email',
  firstName: 'first_name',
  lastName: 'last_name',
};

const FULFILLMENT_RULES: MappingRules = {
  id: 'id',
  status: 'status',
  trackingNumber: 'tracking_number',
  trackingUrl: 'tracking_url',
  trackingCompany: 'tracking_company',
  createdAt: 'created_at',
  updatedAt: 'updated_at',
};

const REFUND_RULES: MappingRules = {
  id: 'id',
  createdAt: 'created_at',
  note: 'note',
};

export const ORDER_RULES: MappingRules = {
  id: 'id',
  name: 'name',
  orderNumber: 'order_number',
  confirmationNumber: 'confirmation_number',
  orderStatusUrl: 'order_status_url',
  email: 'email',
  phone: 'phone',
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  processedAt: 'processed_at',
  closedAt: 'closed_at',
  cancelledAt: 'cancelled_at',
  cancelReason: 'cancel_reason',
  financialStatus: 'financial_status',
  fulfillmentStatus: 'fulfillment_status',
  totalPrice: 'total_price',
  subtotalPrice: 'subtotal_price',
  totalTax: 'total_tax',
  totalDiscounts: 'total_discounts',
  totalShippingPrice: (src) => {
    const set = src.total_shipping_price_set as Record<string, any>;
    return set?.shop_money?.amount;
  },
  currency: 'currency',
  tags: 'tags',
  note: 'note',
  // Simplified customer info
  customerId: 'customer.id',
  customer: (src) => {
    const customer = src.customer as Record<string, unknown>;
    return customer ? normalize(customer, CUSTOMER_INFO_RULES) : undefined;
  },
  // Simplified line items
  lineItems: (src) => {
    const items = src.line_items as any[];
    return items ? normalizeArray(items, LINE_ITEM_RULES) : undefined;
  },
  // Addresses
  shippingAddress: (src) => {
    const addr = src.shipping_address as Record<string, unknown>;
    return addr ? normalize(addr, ADDRESS_RULES) : undefined;
  },
  billingAddress: (src) => {
    const addr = src.billing_address as Record<string, unknown>;
    return addr ? normalize(addr, ADDRESS_RULES) : undefined;
  },
  // Fulfillments
  fulfillments: (src) => {
    const fulfillments = src.fulfillments as any[];
    return fulfillments ? normalizeArray(fulfillments, FULFILLMENT_RULES) : undefined;
  },
  // Refunds
  refunds: (src) => {
    const refunds = src.refunds as any[];
    return refunds ? normalizeArray(refunds, REFUND_RULES) : undefined;
  },
  // Discount codes
  discountCodes: 'discount_codes',
};

/**
 * Normalize a list response that contains items and pagination info.
 */
export function normalizeListResponse(
  response: Record<string, unknown>,
  itemsKey: string,
  itemMapping: MappingRules
): Record<string, unknown> {
  const items = response[itemsKey] as any[];
  const normalized = normalizeArray(items, itemMapping);
  
  const result: Record<string, unknown> = {
    items: normalized,
    count: normalized.length,
  };
  
  // Include pagination info if present
  const linkHeader = response._linkHeader as string;
  if (linkHeader) {
    result.pagination = parseLinkHeader(linkHeader);
  }
  
  return result;
}

/**
 * Parse Shopify's Link header for pagination cursors.
 */
function parseLinkHeader(linkHeader: string): Record<string, unknown> {
  const pagination: Record<string, string> = {};
  
  const links = linkHeader.split(',');
  for (const link of links) {
    const match = link.match(/<[^>]*[?&]page_info=([^&>]+)[^>]*>;\s*rel="([^"]+)"/);
    if (match) {
      const [, cursor, rel] = match;
      pagination[`${rel}Cursor`] = cursor;
    }
  }
  
  return Object.keys(pagination).length > 0 ? pagination : {};
}

/**
 * Normalize a single item response.
 */
export function normalizeItemResponse(
  response: Record<string, unknown>,
  itemKey: string,
  itemMapping: MappingRules
): Record<string, unknown> {
  const item = response[itemKey] as Record<string, unknown>;
  return item ? normalize(item, itemMapping) : {};
}
