/**
 * Tests for auto-pagination transport
 *
 * These tests mirror the Python client's test_transport_auto_pagination.py
 */

import { beforeEach, describe, expect, it } from 'vitest';
import {
  createPaginatedFetch,
  extractPaginationInfo,
  hasExplicitPageParam,
  normalizePaginationValues,
} from '../../src/transport/pagination.js';
import { createMockFetch, type MockFetch, sentRequest } from '../helpers/mockFetch.js';

describe('hasExplicitPageParam', () => {
  it('should detect page param in URL', () => {
    expect(hasExplicitPageParam('https://api.example.com/products?page=2')).toBe(true);
    expect(hasExplicitPageParam('https://api.example.com/products?page=1&limit=50')).toBe(true);
    expect(hasExplicitPageParam('/products?page=5')).toBe(true);
  });

  it('should return false when no page param', () => {
    expect(hasExplicitPageParam('https://api.example.com/products')).toBe(false);
    expect(hasExplicitPageParam('https://api.example.com/products?limit=50')).toBe(false);
    expect(hasExplicitPageParam('/products')).toBe(false);
  });
});

describe('extractPaginationInfo', () => {
  it('should extract pagination from X-Pagination header', () => {
    const headers = new Headers({
      'X-Pagination': JSON.stringify({
        page: 1,
        total_pages: 5,
        total_items: 100,
        per_page: 20,
      }),
    });
    const info = extractPaginationInfo(headers, {});
    expect(info).toEqual({
      page: 1,
      total_pages: 5,
      total_items: 100,
      per_page: 20,
    });
  });

  it('should extract pagination from individual headers', () => {
    const headers = new Headers({
      'X-Total-Pages': '5',
      'X-Current-Page': '2',
    });
    const info = extractPaginationInfo(headers, {});
    expect(info).toEqual({
      page: 2,
      total_pages: 5,
    });
  });

  it('should extract pagination from response body', () => {
    const headers = new Headers();
    const body = {
      data: [],
      pagination: {
        page: 3,
        total_pages: 10,
        total_items: 250,
      },
    };
    const info = extractPaginationInfo(headers, body);
    expect(info).toEqual({
      page: 3,
      total_pages: 10,
      total_items: 250,
    });
  });

  it('should extract pagination from meta.pagination in body', () => {
    const headers = new Headers();
    const body = {
      data: [],
      meta: {
        pagination: {
          page: 1,
          total_pages: 3,
        },
      },
    };
    const info = extractPaginationInfo(headers, body);
    expect(info).toEqual({
      page: 1,
      total_pages: 3,
    });
  });

  it('should return null when no pagination info', () => {
    const headers = new Headers();
    const body = { data: [] };
    const info = extractPaginationInfo(headers, body);
    expect(info).toBeNull();
  });
});

describe('createPaginatedFetch', () => {
  let mockFetch: MockFetch;

  beforeEach(() => {
    mockFetch = createMockFetch();
  });

  describe('Auto-pagination disabled conditions', () => {
    it('should not paginate non-GET requests', async () => {
      const response = new Response(JSON.stringify({ success: true }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products', { method: 'POST' });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith('https://api.example.com/products', {
        method: 'POST',
      });
    });

    it('should not paginate when explicit page param is present (page > 1)', async () => {
      const response = new Response(
        JSON.stringify({ data: [{ id: 1 }], pagination: { page: 2, total_pages: 5 } }),
        { status: 200 }
      );
      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?page=2');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith('https://api.example.com/products?page=2', undefined);
    });

    it('should not paginate when page=1 is explicitly set', async () => {
      // ANY explicit page param disables auto-pagination, including page=1
      const response = new Response(
        JSON.stringify({ data: [{ id: 1 }], pagination: { page: 1, total_pages: 5 } }),
        { status: 200 }
      );
      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?page=1');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith('https://api.example.com/products?page=1', undefined);
    });

    it('should not paginate when autoPagination is disabled', async () => {
      const response = new Response(
        JSON.stringify({ data: [{ id: 1 }], pagination: { page: 1, total_pages: 5 } }),
        { status: 200 }
      );
      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch, { autoPagination: false });
      await paginatedFetch('https://api.example.com/products');

      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Auto-pagination enabled', () => {
    it('should collect all pages when auto-paginating', async () => {
      // Page 1: 2 items, total 3 pages
      const page1Response = new Response(
        JSON.stringify({
          data: [{ id: 1 }, { id: 2 }],
          pagination: { page: 1, total_pages: 3, per_page: 2 },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );

      // Page 2: 2 items
      const page2Response = new Response(
        JSON.stringify({
          data: [{ id: 3 }, { id: 4 }],
          pagination: { page: 2, total_pages: 3, per_page: 2 },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );

      // Page 3: 1 item (last page)
      const page3Response = new Response(
        JSON.stringify({
          data: [{ id: 5 }],
          pagination: { page: 3, total_pages: 3, per_page: 2 },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );

      mockFetch
        .mockResolvedValueOnce(page1Response)
        .mockResolvedValueOnce(page2Response)
        .mockResolvedValueOnce(page3Response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      const response = await paginatedFetch('https://api.example.com/products');

      expect(mockFetch).toHaveBeenCalledTimes(3);

      const body = await response.json();
      expect(body.data).toHaveLength(5);
      expect(body.data.map((item: { id: number }) => item.id)).toEqual([1, 2, 3, 4, 5]);
      expect(body.pagination).toEqual({
        total_pages: 3,
        collected_pages: 3,
        total_items: 5,
        auto_paginated: true,
      });
    });

    it('should stop at maxPages limit', async () => {
      // Create responses for pages 1-5
      const createPageResponse = (page: number) =>
        new Response(
          JSON.stringify({
            data: [{ id: page }],
            pagination: { page, total_pages: 100, per_page: 1 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );

      mockFetch.mockImplementation(() => {
        const callCount = mockFetch.mock.calls.length;
        return Promise.resolve(createPageResponse(callCount));
      });

      const paginatedFetch = createPaginatedFetch(mockFetch, {
        pagination: { maxPages: 3, defaultPageSize: 250 },
      });
      const response = await paginatedFetch('https://api.example.com/products');

      expect(mockFetch).toHaveBeenCalledTimes(3);

      const body = await response.json();
      expect(body.data).toHaveLength(3);
    });

    it('should stop at maxItems limit', async () => {
      // Page with 5 items, but maxItems is 3
      const page1Response = new Response(
        JSON.stringify({
          data: [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }, { id: 5 }],
          pagination: { page: 1, total_pages: 10, per_page: 5 },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );

      mockFetch.mockResolvedValueOnce(page1Response);

      const paginatedFetch = createPaginatedFetch(mockFetch, {
        pagination: { maxItems: 3, maxPages: 100, defaultPageSize: 250 },
      });
      const response = await paginatedFetch('https://api.example.com/products');

      const body = await response.json();
      expect(body.data).toHaveLength(3);
      expect(body.data.map((item: { id: number }) => item.id)).toEqual([1, 2, 3]);
    });

    it('should stop when empty page is returned', async () => {
      const page1Response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 5, per_page: 1 },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );

      const emptyPageResponse = new Response(
        JSON.stringify({
          data: [],
          pagination: { page: 2, total_pages: 5, per_page: 1 },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );

      mockFetch.mockResolvedValueOnce(page1Response).mockResolvedValueOnce(emptyPageResponse);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      const response = await paginatedFetch('https://api.example.com/products');

      expect(mockFetch).toHaveBeenCalledTimes(2);

      const body = await response.json();
      expect(body.data).toHaveLength(1);
    });

    it('should return error response without pagination', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'Not Found' }), { status: 404 });
      mockFetch.mockResolvedValueOnce(errorResponse);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      const response = await paginatedFetch('https://api.example.com/products');

      expect(response.status).toBe(404);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should handle response without pagination info', async () => {
      const response = new Response(JSON.stringify({ data: [{ id: 1 }, { id: 2 }] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      const result = await paginatedFetch('https://api.example.com/products');

      const body = await result.json();
      expect(body.data).toHaveLength(2);
      expect(body.pagination).toBeUndefined();
    });
  });

  describe('URL handling', () => {
    it('should properly add page parameter to URL', async () => {
      const page1Response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 2, per_page: 1 },
        }),
        { status: 200 }
      );

      const page2Response = new Response(
        JSON.stringify({
          data: [{ id: 2 }],
          pagination: { page: 2, total_pages: 2, per_page: 1 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(page1Response).mockResolvedValueOnce(page2Response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?limit=50');

      // Check that page was added to URL
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockFetch.mock.calls[0][0]).toContain('page=1');
      expect(mockFetch.mock.calls[1][0]).toContain('page=2');
      // Original limit should be preserved (caller's choice)
      expect(mockFetch.mock.calls[0][0]).toContain('limit=50');
    });

    it('should use limit=250 when no limit specified', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 1, per_page: 250 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products');

      // Should use default limit of 250 (Katana's max)
      expect(mockFetch.mock.calls[0][0]).toContain('limit=250');
    });

    it('should respect caller specified limit', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 1, per_page: 100 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?limit=100');

      // Should use caller's limit of 100
      expect(mockFetch.mock.calls[0][0]).toContain('limit=100');
    });

    it('should fall back to default limit when limit is invalid', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 1, per_page: 250 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?limit=abc');

      // Should fall back to default limit of 250 for invalid limit
      expect(mockFetch.mock.calls[0][0]).toContain('limit=250');
    });

    it('should fall back to default limit when limit is negative', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 1, per_page: 250 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?limit=-50');

      // Should fall back to default limit of 250 for negative limit
      expect(mockFetch.mock.calls[0][0]).toContain('limit=250');
    });

    it('should fall back to default limit when limit is zero', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 1, per_page: 250 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products?limit=0');

      // Should fall back to default limit of 250 for zero limit
      expect(mockFetch.mock.calls[0][0]).toContain('limit=250');
    });

    it('should handle relative URLs', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 1, per_page: 1 },
        }),
        { status: 200 }
      );

      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('/products');

      // Should use default limit=250 and add page=1
      expect(mockFetch).toHaveBeenCalledWith('/products?page=1&limit=250', undefined);
    });
  });
});

describe('normalizePaginationValues', () => {
  it('converts numeric strings to integers and boolean strings to booleans', () => {
    expect(
      normalizePaginationValues({
        page: '5',
        total_pages: '41',
        total_records: 1000.0,
        first_page: 'false',
        last_page: 'TRUE',
      })
    ).toEqual({
      page: 5,
      total_pages: 41,
      total_records: 1000,
      first_page: false,
      last_page: true,
    });
  });

  it('drops unparseable values so fallbacks apply', () => {
    expect(normalizePaginationValues({ page: 'abc', last_page: 'maybe', other: 'x' })).toEqual({
      other: 'x',
    });
  });

  it('normalises Katana X-Pagination string values via extractPaginationInfo', () => {
    const headers = new Headers({
      'X-Pagination': JSON.stringify({ total_pages: '41', page: '5', last_page: 'false' }),
    });
    expect(extractPaginationInfo(headers, {})).toEqual({
      total_pages: 41,
      page: 5,
      last_page: false,
    });
  });

  it('ignores a non-object X-Pagination header', () => {
    const headers = new Headers({ 'X-Pagination': '[1,2]', 'X-Total-Pages': '3' });
    expect(extractPaginationInfo(headers, {})).toEqual({ total_pages: 3 });
  });
});

describe('createPaginatedFetch — Python PaginationTransport parity', () => {
  let mockFetch: MockFetch;

  beforeEach(() => {
    mockFetch = createMockFetch();
  });

  function page(body: unknown, headers: Record<string, string> = {}, status = 200): Response {
    return new Response(JSON.stringify(body), { status, headers });
  }

  it('returns a single-resource response untouched (no pagination envelope)', async () => {
    mockFetch.mockResolvedValueOnce(page({ id: 1, name: 'Widget' }, { 'X-Custom': 'kept' }));

    const response = await createPaginatedFetch(mockFetch)('https://api.example.com/products/1');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(await response.json()).toEqual({ id: 1, name: 'Widget' });
    expect(response.headers.get('X-Custom')).toBe('kept');
  });

  it('keeps extra top-level fields of an unpaginated list response', async () => {
    mockFetch.mockResolvedValueOnce(page({ data: [{ id: 1 }], meta: { note: 'hi' } }));

    const response = await createPaginatedFetch(mockFetch)('https://api.example.com/things');

    expect(await response.json()).toEqual({ data: [{ id: 1 }], meta: { note: 'hi' } });
  });

  it('truncates an unpaginated list to maxItems, preserving its shape', async () => {
    mockFetch.mockResolvedValueOnce(page({ data: [1, 2, 3, 4], extra: true }));
    mockFetch.mockResolvedValueOnce(page([1, 2, 3, 4]));
    const paginated = createPaginatedFetch(mockFetch, { pagination: { maxItems: 2 } });

    expect(await (await paginated('https://api.example.com/a')).json()).toEqual({
      data: [1, 2],
      extra: true,
    });
    expect(await (await paginated('https://api.example.com/b')).json()).toEqual([1, 2]);
  });

  it('preserves a raw-array body shape when combining pages', async () => {
    mockFetch
      .mockResolvedValueOnce(page([{ id: 1 }], { 'X-Pagination': '{"page":1,"total_pages":2}' }))
      .mockResolvedValueOnce(page([{ id: 2 }], { 'X-Pagination': '{"page":2,"total_pages":2}' }));

    const response = await createPaginatedFetch(mockFetch)('https://api.example.com/bin_locations');

    expect(await response.json()).toEqual([{ id: 1 }, { id: 2 }]);
  });

  it('compares string page counts numerically ("5" vs "41")', async () => {
    mockFetch.mockImplementation((input) => {
      const pageNum = Number(
        new URL(input instanceof Request ? input.url : input).searchParams.get('page')
      );
      return Promise.resolve(
        page(
          { data: [{ id: pageNum }] },
          { 'X-Pagination': JSON.stringify({ page: String(pageNum), total_pages: '41' }) }
        )
      );
    });

    const response = await createPaginatedFetch(mockFetch, {
      pagination: { maxPages: 6 },
    })('https://api.example.com/products');

    // A lexicographic compare would stop at page 5 ("5" >= "41").
    expect(mockFetch).toHaveBeenCalledTimes(6);
    const body = await response.json();
    expect(body.pagination.collected_pages).toBe(6);
  });

  it('returns a non-200 success status as-is (only 200 is paginated)', async () => {
    mockFetch.mockResolvedValueOnce(page({ data: [] }, {}, 203));
    const response = await createPaginatedFetch(mockFetch)('https://api.example.com/products');
    expect(response.status).toBe(203);
  });

  it('returns a non-JSON page with its body still readable', async () => {
    mockFetch.mockResolvedValueOnce(new Response('plain text', { status: 200 }));
    const response = await createPaginatedFetch(mockFetch)('https://api.example.com/export');
    expect(await response.text()).toBe('plain text');
  });

  it('returns an error page mid-pagination as-is', async () => {
    mockFetch
      .mockResolvedValueOnce(page({ data: [{ id: 1 }], pagination: { page: 1, total_pages: 3 } }))
      .mockResolvedValueOnce(page({ message: 'boom' }, {}, 500));
    const response = await createPaginatedFetch(mockFetch)('https://api.example.com/products');
    expect(response.status).toBe(500);
  });

  it('paginates a GET Request (SDK style), keeping headers and other params', async () => {
    mockFetch
      .mockResolvedValueOnce(page({ data: [{ id: 1 }], pagination: { page: 1, total_pages: 2 } }))
      .mockResolvedValueOnce(page({ data: [{ id: 2 }], pagination: { page: 2, total_pages: 2 } }));
    const request = new Request('https://api.example.com/products?ids=1&ids=2', {
      headers: { Authorization: 'Bearer k' },
    });

    const response = await createPaginatedFetch(mockFetch)(request);

    const sent = mockFetch.mock.calls.map((_, i) => sentRequest(mockFetch, i));
    expect(sent[1].url).toBe('https://api.example.com/products?ids=1&ids=2&page=2&limit=250');
    expect(sent[1].headers.get('Authorization')).toBe('Bearer k');
    expect((await response.json()).data).toEqual([{ id: 1 }, { id: 2 }]);
  });

  it('never paginates a POST Request (SDK style)', async () => {
    mockFetch.mockResolvedValueOnce(page({ id: 1 }));
    const request = new Request('https://api.example.com/products', { method: 'POST', body: '{}' });

    await createPaginatedFetch(mockFetch)(request);

    expect(mockFetch).toHaveBeenCalledWith(request, undefined);
  });

  it('reports collected_pages equal to maxPages when the cap is hit', async () => {
    mockFetch.mockImplementation(() =>
      Promise.resolve(page({ data: [{ id: 1 }], pagination: { total_pages: 99 } }))
    );
    const response = await createPaginatedFetch(mockFetch, { pagination: { maxPages: 3 } })(
      'https://api.example.com/products'
    );
    expect((await response.json()).pagination.collected_pages).toBe(3);
  });
});
