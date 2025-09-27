export function validateIntercomToken(token: string): boolean {
  if (!token) return false;

  // Intercom tokens are typically Bearer tokens or direct access tokens
  return token.startsWith('Bearer ') || token.match(/^[a-zA-Z0-9_-]+$/) !== null;
}

export function validateContactId(contactId: string): boolean {
  return typeof contactId === 'string' && contactId.length > 0;
}

export function validateConversationId(conversationId: string): boolean {
  return typeof conversationId === 'string' && conversationId.length > 0;
}

export function validateCompanyId(companyId: string): boolean {
  return typeof companyId === 'string' && companyId.length > 0;
}

export function validateMessageId(messageId: string): boolean {
  return typeof messageId === 'string' && messageId.length > 0;
}

export function validateTagId(tagId: string): boolean {
  return typeof tagId === 'string' && tagId.length > 0;
}

export function validateArticleId(articleId: string): boolean {
  return typeof articleId === 'string' && articleId.length > 0;
}

export function validateTeamId(teamId: string): boolean {
  return typeof teamId === 'string' && teamId.length > 0;
}

export function validateAdminId(adminId: string): boolean {
  return typeof adminId === 'string' && adminId.length > 0;
}

export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return typeof email === 'string' && emailRegex.test(email);
}

export function validateUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function validatePaginationParams(
  page?: number,
  perPage?: number,
): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (page !== undefined) {
    if (typeof page !== 'number' || page < 1) {
      errors.push('Page must be a positive number starting from 1');
    }
  }

  if (perPage !== undefined) {
    if (typeof perPage !== 'number' || perPage < 1 || perPage > 150) {
      errors.push('Per page must be between 1 and 150');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

export function validateSearchQuery(query: string): boolean {
  return typeof query === 'string' && query.trim().length > 0 && query.length <= 500;
}

export function validateRequiredFields(
  data: Record<string, any>,
  requiredFields: string[],
): { isValid: boolean; missingFields: string[] } {
  const missingFields: string[] = [];

  for (const field of requiredFields) {
    if (data[field] === undefined || data[field] === null || data[field] === '') {
      missingFields.push(field);
    }
  }

  return {
    isValid: missingFields.length === 0,
    missingFields,
  };
}

export function validateIntercomTimestamp(timestamp: number | string): boolean {
  if (typeof timestamp === 'string') {
    timestamp = parseInt(timestamp, 10);
  }

  if (isNaN(timestamp)) return false;

  // Check if it's a valid Unix timestamp (between 1970 and reasonable future date)
  const date = new Date(timestamp * 1000);
  const now = new Date();
  const futureLimit = new Date(now.getFullYear() + 10, now.getMonth(), now.getDate());

  return date.getTime() > 0 && date < futureLimit;
}
