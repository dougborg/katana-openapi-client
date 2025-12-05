/**
 * Tests for error classes and parsing utilities
 */

import { describe, it, expect } from 'vitest';
import {
  KatanaError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  ServerError,
  NetworkError,
  parseError,
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

    it('should store validation details', () => {
      const details = [
        { field: 'name', message: 'Name is required' },
        { field: 'sku', message: 'SKU must be unique', code: 'unique' },
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

  it('should return ValidationError for 422', () => {
    const response = new Response(null, { status: 422 });
    const body = {
      errors: [
        { field: 'name', message: 'Required' },
      ],
    };
    const error = parseError(response, body);
    expect(error).toBeInstanceOf(ValidationError);
    expect((error as ValidationError).details).toHaveLength(1);
    expect((error as ValidationError).details[0].field).toBe('name');
  });

  it('should parse validation details from detail array format', () => {
    const response = new Response(null, { status: 422 });
    const body = {
      detail: [
        { loc: ['body', 'name'], msg: 'field required', type: 'value_error.missing' },
      ],
    };
    const error = parseError(response, body);
    expect(error).toBeInstanceOf(ValidationError);
    expect((error as ValidationError).details[0].field).toBe('body.name');
    expect((error as ValidationError).details[0].message).toBe('field required');
    expect((error as ValidationError).details[0].code).toBe('value_error.missing');
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
});
