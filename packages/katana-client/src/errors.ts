/**
 * Typed error hierarchy for Katana API errors
 *
 * Mirrors the Python client's error handling pattern from katana_client.py
 */

/**
 * Base error class for all Katana API errors
 */
export class KatanaError extends Error {
  public readonly statusCode?: number;
  public readonly response?: Response;
  public readonly body?: unknown;

  constructor(
    message: string,
    options?: {
      statusCode?: number;
      response?: Response;
      body?: unknown;
      cause?: Error;
    }
  ) {
    super(message);
    this.name = 'KatanaError';
    this.statusCode = options?.statusCode;
    this.response = options?.response;
    this.body = options?.body;
    // Store cause in a ES2022-compatible way
    if (options?.cause) {
      (this as { cause?: Error }).cause = options.cause;
    }
  }
}

/**
 * Authentication error (401 Unauthorized)
 */
export class AuthenticationError extends KatanaError {
  constructor(message = 'Authentication failed', options?: { response?: Response; body?: unknown }) {
    super(message, { ...options, statusCode: 401 });
    this.name = 'AuthenticationError';
  }
}

/**
 * Rate limit error (429 Too Many Requests)
 */
export class RateLimitError extends KatanaError {
  public readonly retryAfter?: number;

  constructor(
    message = 'Rate limit exceeded',
    options?: { response?: Response; body?: unknown; retryAfter?: number }
  ) {
    super(message, { ...options, statusCode: 429 });
    this.name = 'RateLimitError';
    this.retryAfter = options?.retryAfter;
  }
}

/**
 * Validation error details from the API
 */
export interface ValidationErrorDetail {
  field?: string;
  message: string;
  code?: string;
  value?: unknown;
}

/**
 * Validation error (422 Unprocessable Entity)
 */
export class ValidationError extends KatanaError {
  public readonly details: ValidationErrorDetail[];

  constructor(
    message = 'Validation failed',
    options?: { response?: Response; body?: unknown; details?: ValidationErrorDetail[] }
  ) {
    super(message, { ...options, statusCode: 422 });
    this.name = 'ValidationError';
    this.details = options?.details ?? [];
  }
}

/**
 * Server error (5xx)
 */
export class ServerError extends KatanaError {
  constructor(
    message = 'Server error',
    options?: { statusCode?: number; response?: Response; body?: unknown }
  ) {
    super(message, { ...options, statusCode: options?.statusCode ?? 500 });
    this.name = 'ServerError';
  }
}

/**
 * Network error (connection failures, timeouts, etc.)
 */
export class NetworkError extends KatanaError {
  constructor(message = 'Network error', options?: { cause?: Error }) {
    super(message, options);
    this.name = 'NetworkError';
  }
}

/**
 * Parse an API error response into the appropriate typed error
 */
export function parseError(response: Response, body?: unknown): KatanaError {
  const status = response.status;

  if (status === 401) {
    return new AuthenticationError('Authentication failed - check your API key', {
      response,
      body,
    });
  }

  if (status === 429) {
    const retryAfterHeader = response.headers.get('Retry-After');
    const retryAfter = retryAfterHeader ? parseInt(retryAfterHeader, 10) : undefined;
    return new RateLimitError('Rate limit exceeded - retry after delay', {
      response,
      body,
      retryAfter,
    });
  }

  if (status === 422) {
    const details = parseValidationDetails(body);
    return new ValidationError('Validation failed', {
      response,
      body,
      details,
    });
  }

  if (status >= 500) {
    return new ServerError(`Server error (${status})`, {
      statusCode: status,
      response,
      body,
    });
  }

  // Generic client error
  const message = typeof body === 'object' && body !== null && 'message' in body
    ? String((body as Record<string, unknown>).message)
    : `Request failed with status ${status}`;

  return new KatanaError(message, {
    statusCode: status,
    response,
    body,
  });
}

/**
 * Parse validation error details from response body
 */
function parseValidationDetails(body: unknown): ValidationErrorDetail[] {
  if (!body || typeof body !== 'object') {
    return [];
  }

  const bodyObj = body as Record<string, unknown>;

  // Handle Katana's error format
  if (Array.isArray(bodyObj.errors)) {
    return bodyObj.errors.map((err: unknown) => {
      if (typeof err === 'object' && err !== null) {
        const errObj = err as Record<string, unknown>;
        return {
          field: typeof errObj.field === 'string' ? errObj.field : undefined,
          message: typeof errObj.message === 'string' ? errObj.message : String(err),
          code: typeof errObj.code === 'string' ? errObj.code : undefined,
          value: errObj.value,
        };
      }
      return { message: String(err) };
    });
  }

  // Handle detail array format
  if (Array.isArray(bodyObj.detail)) {
    return bodyObj.detail.map((detail: unknown) => {
      if (typeof detail === 'object' && detail !== null) {
        const detailObj = detail as Record<string, unknown>;
        return {
          field: Array.isArray(detailObj.loc) ? detailObj.loc.join('.') : undefined,
          message: typeof detailObj.msg === 'string' ? detailObj.msg : String(detail),
          code: typeof detailObj.type === 'string' ? detailObj.type : undefined,
        };
      }
      return { message: String(detail) };
    });
  }

  return [];
}
