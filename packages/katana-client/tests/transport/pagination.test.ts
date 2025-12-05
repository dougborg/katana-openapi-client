/**
 * Tests for auto-pagination transport
 *
 * These tests mirror the Python client's test_transport_auto_pagination.py
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  createPaginatedFetch,
  extractPaginationInfo,
  hasExplicitPageParam,
} from '../../src/transport/pagination.js';

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
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
  });

  describe('Auto-pagination disabled conditions', () => {
    it('should not paginate non-GET requests', async () => {
      const response = new Response(JSON.stringify({ success: true }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const paginatedFetch = createPaginatedFetch(mockFetch);
      await paginatedFetch('https://api.example.com/products', { method: 'POST' });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith('https://api.example.com/products', { method: 'POST' });
    });

    it('should not paginate when explicit page param is present', async () => {
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
      // Original limit should be preserved
      expect(mockFetch.mock.calls[0][0]).toContain('limit=50');
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

      expect(mockFetch).toHaveBeenCalledWith('/products?page=1', undefined);
    });
  });
});
