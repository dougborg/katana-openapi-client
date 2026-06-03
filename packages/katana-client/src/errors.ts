/**
 * Typed error hierarchy for Katana API errors
 *
 * Mirrors the Python client's error handling pattern from katana_client.py
 */

import type { ValidationErrorDetail } from './generated/types.gen.js';

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
  constructor(
    message = 'Authentication failed',
    options?: { response?: Response; body?: unknown }
  ) {
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
 * Validation error (422 Unprocessable Entity)
 *
 * `details` carries the Ajv-style validation error array exactly as Katana
 * sends it — each item is `{ path, code, message, info }` where `code` is the
 * failed Ajv keyword and `info` holds keyword-specific params (see
 * `ValidationErrorDetail` in the generated types). The structured array is the
 * stable, programmatic contract; the human-readable `message` is built by
 * `formatValidationDetail`, which mirrors the Python client's
 * `_format_ajv_detail` wording for cross-runtime parity.
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
    const retryAfter = retryAfterHeader ? Number.parseInt(retryAfterHeader, 10) : undefined;
    return new RateLimitError('Rate limit exceeded - retry after delay', {
      response,
      body,
      retryAfter,
    });
  }

  if (status === 422) {
    const details = parseValidationDetails(body);
    const base = extractMessage(body) ?? 'Validation failed';
    const message = buildValidationMessage(base, details);
    return new ValidationError(message, {
      response,
      body,
      details,
    });
  }

  if (status >= 500) {
    return new ServerError(extractMessage(body) ?? `Server error (${status})`, {
      statusCode: status,
      response,
      body,
    });
  }

  // Generic client error — surface the body's message even for statuses the
  // spec doesn't document, unwrapping Katana's nested `{ "error": {...} }`.
  const message = extractMessage(body) ?? `Request failed with status ${status}`;

  return new KatanaError(message, {
    statusCode: status,
    response,
    body,
  });
}

/**
 * Unwrap Katana's nested `{ "error": {...} }` envelope. Some endpoints wrap the
 * error fields under a top-level `error` key; most return them flat. Returns the
 * object carrying `message` / `name` / `details`, or `undefined` for non-objects.
 *
 * Mirrors the Python client's `_extract_error_fields` / `_try_parse_error_body`.
 */
function unwrapErrorEnvelope(body: unknown): Record<string, unknown> | undefined {
  if (!body || typeof body !== 'object') {
    return undefined;
  }
  const obj = body as Record<string, unknown>;
  const inner = obj.error;
  if (inner && typeof inner === 'object' && !Array.isArray(inner)) {
    return inner as Record<string, unknown>;
  }
  return obj;
}

/**
 * Pull a human-readable message out of an (optionally enveloped) error body.
 */
function extractMessage(body: unknown): string | undefined {
  const core = unwrapErrorEnvelope(body);
  return core && typeof core.message === 'string' ? core.message : undefined;
}

/**
 * Runtime guard for an Ajv-style validation detail (`BaseValidationError` shape).
 */
function isValidationDetail(value: unknown): value is ValidationErrorDetail {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.path === 'string' && typeof obj.code === 'string' && typeof obj.message === 'string'
  );
}

/**
 * Parse the Ajv-style `details[]` array from a 422 body (envelope-aware).
 */
function parseValidationDetails(body: unknown): ValidationErrorDetail[] {
  const core = unwrapErrorEnvelope(body);
  if (!core || !Array.isArray(core.details)) {
    return [];
  }
  return core.details.filter(isValidationDetail);
}

/**
 * Combine the base error message with one formatted line per validation detail.
 * Mirrors the Python client's `ValidationError.__str__` (base message, then a
 * newline-joined block of `_format_ajv_detail` lines).
 */
function buildValidationMessage(base: string, details: ValidationErrorDetail[]): string {
  if (details.length === 0) {
    return base;
  }
  return `${base}\n${details.map(formatValidationDetail).join('\n')}`;
}

/**
 * Render one Ajv-style validation detail as a human-readable line, dispatching
 * on the Ajv keyword (`code`) and reading keyword-specific params from `info`.
 *
 * Mirrors the Python client's `_format_ajv_detail` (utils.py) wording for
 * cross-runtime parity. Reads only `code` + `info` — Katana does not send the
 * offending value (Ajv `data`) on the wire, and neither client needs it.
 */
function formatValidationDetail(detail: ValidationErrorDetail): string {
  // `path` is Ajv's instancePath; drop the leading separator — JSON Pointer "/"
  // (the live wire format) or the legacy dotted "." form the schema also documents —
  // so the field name reads cleanly either way.
  const field = detail.path.replace(/^[/.]+/, '');
  // `info` is read as a loose record (the union isn't narrowed by `code` here), so
  // each branch validates the params it needs and falls through to the generic
  // formatter below when they're missing or the wrong type — e.g. a
  // GenericValidationError carrying an unexpected `code` and no `info`. This keeps a
  // malformed detail from rendering "must not exceed undefined characters".
  const info = ((detail as { info?: unknown }).info ?? {}) as Record<string, unknown>;
  const isNum = (v: unknown): v is number => typeof v === 'number';
  const isStr = (v: unknown): v is string => typeof v === 'string';

  switch (detail.code) {
    // String / format keywords
    case 'maxLength':
      if (isNum(info.limit)) return `  Field '${field}' must not exceed ${info.limit} characters`;
      break;
    case 'minLength':
      if (isNum(info.limit)) return `  Field '${field}' must be at least ${info.limit} characters`;
      break;
    case 'format':
      if (isStr(info.format)) return `  Field '${field}' must match format: ${info.format}`;
      break;
    case 'pattern':
      if (isStr(info.pattern)) return `  Field '${field}' must match pattern: ${info.pattern}`;
      break;

    // Numeric keywords
    case 'minimum':
      if (isNum(info.limit)) return `  Field '${field}' must be >= ${info.limit}`;
      break;
    case 'maximum':
      if (isNum(info.limit)) return `  Field '${field}' must be <= ${info.limit}`;
      break;
    case 'exclusiveMinimum':
      if (isNum(info.limit)) return `  Field '${field}' must be > ${info.limit}`;
      break;
    case 'exclusiveMaximum':
      if (isNum(info.limit)) return `  Field '${field}' must be < ${info.limit}`;
      break;
    case 'multipleOf':
      if (isNum(info.multipleOf))
        return `  Field '${field}' must be a multiple of ${info.multipleOf}`;
      break;

    // Array keywords
    case 'minItems':
      if (isNum(info.limit)) return `  Field '${field}' must have at least ${info.limit} items`;
      break;
    case 'maxItems':
      if (isNum(info.limit)) return `  Field '${field}' must have at most ${info.limit} items`;
      break;
    case 'uniqueItems':
      if (isNum(info.i) && isNum(info.j))
        return `  Field '${field}' contains duplicate items at indices ${info.i} and ${info.j}`;
      break;

    // Object keywords
    case 'required':
      if (isStr(info.missingProperty)) return `  Missing required field: '${info.missingProperty}'`;
      break;
    case 'additionalProperties':
      if (isStr(info.additionalProperty))
        return `  Field '${field}' has unexpected property: '${info.additionalProperty}'`;
      break;
    case 'dependencies':
      if (isStr(info.property) && isStr(info.missingProperty))
        return `  Field '${field}' has property '${info.property}' but is missing dependent property '${info.missingProperty}'`;
      break;

    // Type / composition keywords
    case 'type':
      if (isStr(info.type)) return `  Field '${field}' must be of type: ${info.type}`;
      break;
    case 'enum':
      if (Array.isArray(info.allowedValues))
        return `  Field '${field}' must be one of: ${formatAllowedValues(info.allowedValues)}`;
      break;
    case 'const':
      if ('allowedValue' in info)
        return `  Field '${field}' must equal: ${JSON.stringify(info.allowedValue)}`;
      break;
    case 'oneOf': {
      const passing = info.passingSchemas;
      if (passing === null || passing === undefined) {
        return `  Field '${field}' did not match any allowed schema`;
      }
      if (Array.isArray(passing))
        return `  Field '${field}' matched multiple allowed schemas (indices ${formatAllowedValues(passing)}); must match exactly one`;
      break;
    }
  }

  // Generic fallback: GenericValidationError, an unknown/future keyword, or a typed
  // keyword whose params were missing or malformed.
  const prefix = detail.code ? `(${detail.code}) ` : '';
  const suffix = Object.keys(info).length > 0 ? ` — info: ${JSON.stringify(info)}` : '';
  const message = detail.message || '<no message>';
  return `  Field '${field}': ${prefix}${message}${suffix}`;
}

/**
 * Render an `allowedValues` / index list for display (e.g. `enum`, `oneOf`).
 */
function formatAllowedValues(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((v) => (typeof v === 'string' ? v : JSON.stringify(v))).join(', ');
  }
  return String(value);
}
