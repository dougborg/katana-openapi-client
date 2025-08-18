# OpenAPI Documentation

This page contains the complete OpenAPI specification for the Katana Manufacturing ERP
API, rendered with Swagger UI for interactive exploration.

## About the Katana API

The Katana API provides programmatic access to your Katana Manufacturing ERP system,
allowing you to:

- **Manage Products**: Create, read, update, and delete products and variants
- **Inventory Control**: Track inventory levels, movements, and locations
- **Manufacturing Orders**: Create and manage manufacturing orders and operations
- **Purchase Orders**: Handle supplier relationships and purchase order management
- **Sales Orders**: Process customer orders and fulfillment
- **And Much More**: Complete access to all Katana functionality

## Interactive API Explorer

Use the interactive API explorer below to:

- **Browse endpoints** organized by category
- **View request/response schemas** with detailed type information
- **Test API calls** directly from the documentation (with proper authentication)
- **Explore examples** for each endpoint

!!! tip "API Authentication" To test API calls through this interface, you'll need to:

```
1. Click the **Authorize** button in the Swagger UI below
2. Enter your API key in the format: `Bearer YOUR_API_KEY_HERE`
3. Your API key can be found in your Katana account settings
```

!!! info "Base URLs" - **Production**: `https://api.katanamrp.com` - **Demo/Testing**:
Use your specific Katana instance URL

______________________________________________________________________

<swagger-ui src="katana-openapi.yaml"/>

## Need Help?

- **Client Documentation**: See our [KatanaClient Guide](KATANA_CLIENT_GUIDE.md) for
  Python-specific usage
- **Rate Limiting**: The API has rate limits - our client handles this automatically
- **Pagination**: Large result sets are paginated - our client auto-paginates
- **Error Handling**: See the API responses above for error codes and messages

## OpenAPI Specification

The complete OpenAPI specification is available at:
[`katana-openapi.yaml`](katana-openapi.yaml)

This specification includes:

- **103 API endpoints** across all Katana modules
- **Complete request/response schemas** with validation rules
- **Authentication requirements** for each endpoint
- **Real-world examples** for all operations
