# ADR-004: Defer Observability to httpx

## Status

Accepted

Date: 2024-08-13 (estimated)

## Context

API clients need observability features like:

- Request/response logging
- Metrics (latency, throughput, errors)
- Distributed tracing (OpenTelemetry, Jaeger)
- Custom event hooks

Options for providing observability:

1. **Built-in Observability**: Implement logging, metrics, tracing in the client
1. **Defer to httpx**: Use httpx's native event hooks and let users add their own
1. **Hybrid**: Basic logging built-in, advanced features via httpx

Considerations:

- Users have different observability requirements
- Observability stacks vary (Prometheus, DataDog, New Relic, OpenTelemetry)
- Built-in features become dependencies and maintenance burden
- httpx provides comprehensive event hook system

## Decision

We will **defer observability to httpx's native features** and provide documentation on
how to use them.

The client will:

- NOT include built-in metrics collection
- NOT include built-in tracing
- NOT include opinionated logging beyond basic errors
- DOCUMENT how to use httpx event hooks
- DOCUMENT integration patterns for common tools

Users can add observability via httpx's event hooks:

```python
# Request/Response Logging
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)

# Custom Event Hooks
def log_request(request):
    print(f">>> {request.method} {request.url}")

client.event_hooks["request"] = [log_request]

# OpenTelemetry Integration
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
HTTPXClientInstrumentor().instrument()

# Prometheus Metrics
from prometheus_client import Counter
requests_total = Counter('katana_requests', 'Total requests')

def track_request(request):
    requests_total.inc()

client.event_hooks["request"] = [track_request]
```

## Consequences

### Positive Consequences

1. **Flexibility**: Users choose their observability stack
1. **Zero Dependencies**: No observability libraries required
1. **No Maintenance Burden**: Don't maintain integrations for every tool
1. **Standard Patterns**: Uses httpx patterns, no custom API
1. **Future-Proof**: Works with any new observability tool
1. **Opt-In**: Users only pay for what they use
1. **No Opinions**: Don't force observability choices on users

### Negative Consequences

1. **Setup Required**: Users must configure observability themselves
1. **Documentation Needed**: Must document common patterns
1. **No Out-of-Box**: No built-in dashboards or metrics
1. **Learning Curve**: Users need to learn httpx event hooks

### Neutral Consequences

1. **User Responsibility**: Users own their observability setup
1. **Flexibility = Complexity**: More options means more decisions

## Alternatives Considered

### Alternative 1: Built-in Observability

Include Prometheus metrics, structured logging, etc:

```python
from katana_public_api_client import KatanaClient

client = KatanaClient(
    enable_metrics=True,
    enable_tracing=True,
    log_level="INFO"
)

# Metrics automatically exported to /metrics endpoint
# Traces automatically sent to configured backend
```

**Pros:**

- Works out of the box
- Consistent across users
- Easy to get started

**Cons:**

- Forces specific observability stack
- Adds dependencies (prometheus_client, opentelemetry, etc.)
- Maintenance burden for integrations
- Hard to customize
- Breaks for users with different stacks

**Why Rejected:** Too opinionated, maintenance burden, limits flexibility.

### Alternative 2: Plugin System

Provide plugin system for observability:

```python
from katana_public_api_client.plugins import PrometheusPlugin, OTelPlugin

client = KatanaClient(
    plugins=[
        PrometheusPlugin(),
        OTelPlugin(endpoint="...")
    ]
)
```

**Pros:**

- Opt-in features
- Extensible
- Can maintain official plugins

**Cons:**

- Need to maintain plugin system
- Need to maintain multiple plugins
- Users still need to learn plugin API
- Duplicates httpx's event hooks

**Why Rejected:** Reinvents httpx's existing event hook system.

### Alternative 3: Minimal Logging Only

Include basic structured logging, nothing else:

```python
# Built-in: structured logs
logger.info("API request", extra={
    "method": "GET",
    "url": "/products",
    "status": 200,
    "duration_ms": 123
})
```

**Pros:**

- Useful for debugging
- Low maintenance
- Opt-out with log level

**Cons:**

- Still opinionated about log format
- Doesn't help with metrics/tracing
- Users may want different log formats

**Why Rejected:** Partial solution, still requires users to add metrics/tracing.

## Implementation Details

### Provided Documentation

Document common observability patterns in README:

#### Request/Response Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.DEBUG)

async with KatanaClient() as client:
    # All requests logged automatically
    response = await get_all_products.asyncio_detailed(client=client)
```

#### Custom Event Hooks

```python
def log_request(request):
    print(f">>> {request.method} {request.url}")

def log_response(response):
    print(f"<<< {response.status_code}")

async with KatanaClient() as client:
    client.event_hooks["request"] = [log_request]
    client.event_hooks["response"] = [log_response]
```

#### OpenTelemetry Integration

```python
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

HTTPXClientInstrumentor().instrument()

# All requests now have spans
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(client=client)
```

#### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

requests_total = Counter('katana_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('katana_request_duration_seconds', 'Request duration')

def track_request(request):
    requests_total.labels(method=request.method, endpoint=request.url.path).inc()

def track_response(response):
    request_duration.observe(response.elapsed.total_seconds())

async with KatanaClient() as client:
    client.event_hooks["request"] = [track_request]
    client.event_hooks["response"] = [track_response]
```

### What We Provide

1. **Documentation**: Common integration patterns
1. **Examples**: Working examples in `examples/`
1. **Clean API**: httpx client is directly accessible for advanced use
1. **Event Hooks**: Full access to httpx's event system

### What We Don't Provide

1. ❌ Built-in metrics collection
1. ❌ Built-in tracing
1. ❌ Opinionated logging format
1. ❌ Observability library dependencies

## Educational Resources

Link users to:

- [httpx Event Hooks Documentation](https://www.python-httpx.org/advanced/#event-hooks)
- [OpenTelemetry httpx Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/httpx/httpx.html)
- [Prometheus Python Client](https://github.com/prometheus/client_python)

## References

- [httpx Advanced Features](https://www.python-httpx.org/advanced/)
- [httpx Event Hooks](https://www.python-httpx.org/advanced/#event-hooks)
- [REVISED_ASSESSMENT.md - Observability](../REVISED_ASSESSMENT.md#observability-current-state-is-correct-)
- Issue #30: Cookbook documentation (will include observability examples)
