#!/bin/bash

# Katana API Documentation Crawler
# Downloads comprehensive API documentation for offline reference

set -e

BASE_URL="https://developer.katanamrp.com"
DOCS_DIR="docs/katana-api-reference"

# Ensure directory exists
mkdir -p "$DOCS_DIR"

echo "🔍 Crawling Katana API Documentation..."

# Main API documentation sections
echo "📚 Downloading main API sections..."

# Core API pages
wget -P "$DOCS_DIR" --convert-links --page-requisites --no-parent \
  "$BASE_URL/docs/api/introduction" \
  "$BASE_URL/docs/api/authentication" \
  "$BASE_URL/docs/api/errors" \
  "$BASE_URL/docs/api/pagination" \
  "$BASE_URL/docs/api/rate-limiting" \
  "$BASE_URL/docs/api/webhooks" || true

# Resource documentation - Major entities
echo "📦 Downloading resource documentation..."

# Core business entities
RESOURCES=(
  "products"
  "materials"
  "variants"
  "customers"
  "suppliers"
  "sales-orders"
  "purchase-orders"
  "manufacturing-orders"
  "inventory"
  "inventory-movements"
  "locations"
  "batches"
  "stock-adjustments"
  "stock-transfers"
  "stocktakes"
  "price-lists"
  "bom-rows"
  "recipes"
  "operators"
  "factories"
  "additional-costs"
  "custom-fields"
)

for resource in "${RESOURCES[@]}"; do
  echo "  📄 Downloading $resource documentation..."
  wget -P "$DOCS_DIR" --convert-links --page-requisites --no-parent \
    "$BASE_URL/docs/api/$resource" || true
done

# API reference sections
echo "📖 Downloading API reference..."
wget -P "$DOCS_DIR" --convert-links --page-requisites --no-parent \
  "$BASE_URL/api-reference" || true

# Get the main developer documentation index
echo "🏠 Downloading developer documentation index..."
wget -P "$DOCS_DIR" --convert-links --page-requisites --no-parent \
  "$BASE_URL/docs" || true

# Try to get SDK/code examples
echo "💻 Downloading SDK documentation..."
wget -P "$DOCS_DIR" --convert-links --page-requisites --no-parent \
  "$BASE_URL/docs/sdks" || true

echo "✅ Documentation crawl complete!"
echo "📁 Files saved to: $DOCS_DIR"
echo "📊 Total files downloaded:"
find "$DOCS_DIR" -type f | wc -l
