/**
 * Tests for error classes and parsing utilities
 */

import { describe, expect, it } from 'vitest';
import {
  AuthenticationError,
  KatanaError,
  NetworkError,
  parseError,
  RateLimitError,
  ServerError,
  ValidationError,
} from '../src/errors.js';

describe('Error Classes', () => {
  describe('KatanaError', () => {
    it('should create with message only', () => {
      const error = new KatanaError('Something went wrong');
      expect(error.message).toBe('Something went wrong');
      expect(error.name).toBe('KatanaError');
      expect(error.statusCode).toBeUndefined();
    });

    it('should create with all options', () => {
      const response = new Response(null, { status: 400 });
      const body = { error: 'Bad request' };
      const error = new KatanaError('Bad request', {
        statusCode: 400,
        response,
        body,
      });
      expect(error.statusCode).toBe(400);
      expect(error.response).toBe(response);
      expect(error.body).toEqual(body);
    });

    it('should store cause', () => {
      const cause = new Error('Original error');
      const error = new KatanaError('Wrapped error', { cause });
      expect((error as unknown as { cause: Error }).cause).toBe(cause);
    });
  });

  describe('AuthenticationError', () => {
    it('should have status code 401', () => {
      const error = new AuthenticationError();
      expect(error.statusCode).toBe(401);
      expect(error.name).toBe('AuthenticationError');
    });

    it('should accept custom message', () => {
      const error = new AuthenticationError('Invalid API key');
      expect(error.message).toBe('Invalid API key');
    });
  });

  describe('RateLimitError', () => {
    it('should have status code 429', () => {
      const error = new RateLimitError();
      expect(error.statusCode).toBe(429);
      expect(error.name).toBe('RateLimitError');
    });

    it('should store retryAfter', () => {
      const error = new RateLimitError('Rate limited', { retryAfter: 30 });
      expect(error.retryAfter).toBe(30);
    });
  });

  describe('ValidationError', () => {
    it('should have status code 422', () => {
      const error = new ValidationError();
      expect(error.statusCode).toBe(422);
      expect(error.name).toBe('ValidationError');
    });

    it('should store Ajv-style validation details verbatim', () => {
      const details = [
        { path: '/name', code: 'required', message: 'must have required property', info: {} },
        { path: '/sku', code: 'maxLength', message: 'too long', info: { limit: 40 } },
      ];
      const error = new ValidationError('Validation failed', { details });
      expect(error.details).toEqual(details);
    });

    it('should default to empty details array', () => {
      const error = new ValidationError();
      expect(error.details).toEqual([]);
    });
  });

  describe('ServerError', () => {
    it('should default to status code 500', () => {
      const error = new ServerError();
      expect(error.statusCode).toBe(500);
      expect(error.name).toBe('ServerError');
    });

    it('should accept custom status code', () => {
      const error = new ServerError('Gateway Timeout', { statusCode: 504 });
      expect(error.statusCode).toBe(504);
    });
  });

  describe('NetworkError', () => {
    it('should create with message', () => {
      const error = new NetworkError('Connection refused');
      expect(error.message).toBe('Connection refused');
      expect(error.name).toBe('NetworkError');
    });

    it('should store cause', () => {
      const cause = new Error('ECONNREFUSED');
      const error = new NetworkError('Network error', { cause });
      expect((error as unknown as { cause: Error }).cause).toBe(cause);
    });
  });
});

describe('parseError', () => {
  it('should return AuthenticationError for 401', () => {
    const response = new Response(null, { status: 401 });
    const error = parseError(response);
    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error.statusCode).toBe(401);
  });

  it('should return RateLimitError for 429', () => {
    const headers = new Headers({ 'Retry-After': '30' });
    const response = new Response(null, { status: 429, headers });
    const error = parseError(response);
    expect(error).toBeInstanceOf(RateLimitError);
    expect((error as RateLimitError).retryAfter).toBe(30);
  });

  it("should parse a 422 from Katana's nested {error:{details}} envelope (live wire shape)", () => {
    const response = new Response(null, { status: 422 });
    // Exact shape captured from a live POST /custom_field_definitions 422.
    const body = {
      error: {
        statusCode: 422,
        name: 'UnprocessableEntityError',
        message: 'The request body is invalid. See error object `details` property for more info.',
        code: 'VALIDATION_FAILED',
        details: [
          {
            path: '/label',
            code: 'maxLength',
            message: 'must NOT have more than 255 characters',
            info: { limit: 255 },
          },
        ],
      },
    };
    const error = parseError(response, body) as ValidationError;
    expect(error).toBeInstanceOf(ValidationError);
    // Structured details preserved verbatim (the cross-runtime contract).
    expect(error.details).toHaveLength(1);
    expect(error.details[0]).toEqual({
      path: '/label',
      code: 'maxLength',
      message: 'must NOT have more than 255 characters',
      info: { limit: 255 },
    });
    // Display message: base (from the envelope) + a formatted, path-stripped line.
    expect(error.message).toContain('The request body is invalid');
    expect(error.message).toContain("Field 'label' must not exceed 255 characters");
  });

  it('should format each Ajv keyword family, mirroring the Python wording', () => {
    const response = new Response(null, { status: 422 });
    const body = {
      error: {
        message: 'invalid',
        details: [
          { path: '/sku', code: 'minLength', message: 'short', info: { limit: 3 } },
          {
            path: '/fieldType',
            code: 'enum',
            message: 'bad',
            info: { allowedValues: ['shortText', 'number'] },
          },
          { path: '/price', code: 'minimum', message: 'low', info: { limit: 1, comparison: '>=' } },
          { path: '', code: 'required', message: 'missing', info: { missingProperty: 'status' } },
          { path: '/qty', code: 'type', message: 'wrong', info: { type: 'number' } },
        ],
      },
    };
    const { message } = parseError(response, body) as ValidationError;
    expect(message).toContain("Field 'sku' must be at least 3 characters");
    expect(message).toContain("Field 'fieldType' must be one of: shortText, number");
    expect(message).toContain("Field 'price' must be >= 1");
    expect(message).toContain("Missing required field: 'status'");
    expect(message).toContain("Field 'qty' must be of type: number");
  });

  it('should fall back gracefully for unknown/future keywords', () => {
    const response = new Response(null, { status: 422 });
    const body = {
      error: {
        message: 'invalid',
        details: [{ path: '/x', code: 'futureKeyword', message: 'nope', info: { detail: 1 } }],
      },
    };
    const { message, details } = parseError(response, body) as ValidationError;
    expect(details).toHaveLength(1);
    expect(message).toContain("Field 'x': (futureKeyword) nope");
    expect(message).toContain('info:');
  });

  it('should fall back to generic formatting when a typed keyword is missing its info params', () => {
    const response = new Response(null, { status: 422 });
    // maxLength with no info.limit — must NOT render "must not exceed undefined characters".
    const body = {
      error: {
        message: 'invalid',
        details: [{ path: '/name', code: 'maxLength', message: 'too long' }],
      },
    };
    const { message } = parseError(response, body) as ValidationError;
    expect(message).not.toContain('undefined');
    expect(message).toContain("Field 'name': (maxLength) too long");
  });

  it('should strip a legacy dotted path the same as a JSON pointer', () => {
    const response = new Response(null, { status: 422 });
    const body = {
      error: {
        message: 'invalid',
        details: [{ path: '.city', code: 'maxLength', message: 'too long', info: { limit: 10 } }],
      },
    };
    const { message } = parseError(response, body) as ValidationError;
    expect(message).toContain("Field 'city' must not exceed 10 characters");
  });

  it('should not throw and yield empty details when 422 body lacks details', () => {
    const response = new Response(null, { status: 422 });
    const error = parseError(response, { error: { message: 'bad input' } }) as ValidationError;
    expect(error).toBeInstanceOf(ValidationError);
    expect(error.details).toEqual([]);
    expect(error.message).toBe('bad input');
  });

  it('should return ServerError for 5xx', () => {
    const response = new Response(null, { status: 503 });
    const error = parseError(response);
    expect(error).toBeInstanceOf(ServerError);
    expect(error.statusCode).toBe(503);
  });

  it('should return generic KatanaError for other 4xx', () => {
    const response = new Response(null, { status: 404 });
    const body = { message: 'Product not found' };
    const error = parseError(response, body);
    expect(error).toBeInstanceOf(KatanaError);
    expect(error).not.toBeInstanceOf(AuthenticationError);
    expect(error.message).toBe('Product not found');
    expect(error.statusCode).toBe(404);
  });

  it('should handle missing body message', () => {
    const response = new Response(null, { status: 400 });
    const error = parseError(response);
    expect(error.message).toBe('Request failed with status 400');
  });

  it("should surface a message from Katana's nested {error:{message}} envelope on a 4xx", () => {
    const response = new Response(null, { status: 404 });
    const body = { error: { name: 'NotFoundError', message: 'Product not found' } };
    const error = parseError(response, body);
    expect(error).toBeInstanceOf(KatanaError);
    expect(error).not.toBeInstanceOf(AuthenticationError);
    expect(error.message).toBe('Product not found');
    expect(error.statusCode).toBe(404);
  });

  it('should surface a nested-envelope message for an undocumented 5xx status', () => {
    const response = new Response(null, { status: 599 });
    const error = parseError(response, { error: { message: 'upstream exploded' } });
    expect(error).toBeInstanceOf(ServerError);
    expect(error.message).toBe('upstream exploded');
  });
});
