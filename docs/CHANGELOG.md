# CHANGELOG



## v0.1.0 (2025-07-16)

### Feature

* feat: initial release of katana-openapi-client

🚀 Production-ready Python client for Katana Manufacturing ERP API

✨ Key Features:
- Transport-layer resilience with automatic retries and rate limiting
- Smart auto-pagination for large datasets
- Type-safe async client with full mypy compliance
- Modern Python packaging with Poetry and PEP 621

🏗️ Architecture:
- Clean separation of generated OpenAPI client and custom enhancements
- ResilientAsyncTransport handles all HTTP resilience transparently
- Comprehensive error handling and logging
- Context manager pattern for resource management

🧪 Developer Experience:
- Comprehensive test suite with pytest and async support
- Modern development workflow with poethepoet task runner
- Automated formatting, linting, and type checking
- GitHub Actions CI/CD with semantic release
- Complete documentation and usage guides

🔧 Ready for Production:
- Automatic retry logic with exponential backoff
- Rate limiting with 429 response handling
- Pagination that works transparently with all endpoints
- Environment variable configuration
- Comprehensive error types and handling

Perfect for teams needing reliable integration with Katana Manufacturing ERP! ([`5ce390a`](https://github.com/dougborg/katana-openapi-client/commit/5ce390a604cc6f10993a3a5b416f7b55ef805871))
