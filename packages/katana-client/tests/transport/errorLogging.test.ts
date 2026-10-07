/**
 * Tests for the 4xx error-logging layer (mirrors Python's ErrorLoggingTransport).
 */

import { describe, expect, it, vi } from 'vitest';
import { createErrorLoggingFetch } from '../../src/transport/errorLogging.js';

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('createErrorLoggingFetch', () => {
  it('logs a 4xx with method, sanitised URL and the parsed message', async () => {
    const logger = { error: vi.fn() };
    const base = vi
      .fn<typeof fetch>()
      .mockResolvedValue(json({ message: 'Product not found' }, 404));
    const logged = createErrorLoggingFetch(base, logger);

    const response = await logged('https://api.example.com/products/9?api_key=secret&x=1', {
      method: 'DELETE',
    });

    expect(logger.error).toHaveBeenCalledTimes(1);
    const message = logger.error.mock.calls[0][0] as string;
    expect(message).toContain('Client error 404 for DELETE');
    expect(message).toContain('api_key=***');
    expect(message).not.toContain('secret');
    expect(message).toContain('Product not found');
    // The caller still gets an unread body.
    expect(await response.json()).toEqual({ message: 'Product not found' });
  });

  it('includes the formatted validation details for a 422', async () => {
    const logger = { error: vi.fn() };
    const base = vi.fn<typeof fetch>().mockResolvedValue(
      json(
        {
          error: {
            statusCode: 422,
            name: 'UnprocessableEntityError',
            message: 'The request body is invalid.',
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
        },
        422
      )
    );
    const logged = createErrorLoggingFetch(base, logger);

    await logged(new Request('https://api.example.com/products', { method: 'POST', body: '{}' }));

    const message = logger.error.mock.calls[0][0] as string;
    expect(message).toContain('Client error 422 for POST');
    expect(message).toContain("Field 'label' must not exceed 255 characters");
  });

  it.each([200, 204, 429, 500, 503])('does not log status %i', async (status) => {
    const logger = { error: vi.fn() };
    const base = vi.fn<typeof fetch>().mockResolvedValue(new Response(null, { status }));
    const logged = createErrorLoggingFetch(base, logger);

    await logged('https://api.example.com/products');

    expect(logger.error).not.toHaveBeenCalled();
  });

  it('still logs when the 4xx body is not JSON', async () => {
    const logger = { error: vi.fn() };
    const base = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response('<html>nope</html>', { status: 403 }));
    const logged = createErrorLoggingFetch(base, logger);

    await logged('https://api.example.com/products');

    expect(logger.error.mock.calls[0][0]).toContain('Client error 403 for GET');
  });
});
