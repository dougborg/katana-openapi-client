# Schema Standards Testing

This project includes comprehensive tests to ensure OpenAPI schema quality and
consistency. The test suite validates schema standards and helps track improvement
progress.

## Running Schema Standards Tests

```bash
# Run all schema standards tests
poetry run pytest tests/test_schema_standards.py -v

# Run specific test categories
poetry run pytest tests/test_schema_standards.py::TestSchemaStandards::test_base_entity_inheritance_requirements -v
poetry run pytest tests/test_schema_standards.py::TestSchemaStandards::test_schema_description_requirements -v

# Run with detailed output for progress tracking
poetry run pytest tests/test_schema_standards.py -v -s
```

## Current Schema Standards Compliance

Based on our latest analysis:

- ✅ **BaseEntity Inheritance**: 100% (54/54 entity schemas)
- ✅ **Inheritance Patterns**: Complete coverage with proper entity types
- ✅ **Property Descriptions**: Comprehensive coverage for critical properties
- ✅ **Schema Examples**: Strong coverage for entity schemas (46%)
- ✅ **Endpoint Standards**: All endpoints follow proper response schema patterns
- ✅ **Naming Conventions**: Consistent PascalCase naming
- 🔄 **Schema Descriptions**: In progress (39% completion, 73/183 schemas)

## Schema Standards Enforced

1. **BaseEntity Inheritance**

   - All schemas with `id` properties must inherit from `BaseEntity`
   - Proper use of `UpdatableEntity`, `DeletableEntity`, `ArchivableEntity`
   - Consistent timestamp field inheritance

1. **Documentation Quality**

   - All schemas must have meaningful descriptions (≥20 characters)
   - Properties must have clear, descriptive documentation
   - Examples should be at schema level, not property level

1. **Example Standards**

   - Entity schemas must include comprehensive examples
   - Examples should demonstrate realistic data
   - Property-level examples are discouraged in favor of schema examples

1. **Endpoint Consistency**

   - Response schemas must use `$ref` references, not inline definitions
   - Consistent error response patterns
   - Proper HTTP status code usage

## Benefits of Schema Standards Testing

- **Quality Assurance**: Automated validation prevents schema regressions
- **Developer Experience**: Better documentation and examples improve API usability
- **Code Generation**: Consistent patterns ensure reliable client generation
- **Maintenance**: Systematic approach to schema improvements
- **Documentation**: Self-documenting API with comprehensive examples

## Adding New Schema Tests

To add new schema validation rules:

1. Add test methods to `tests/test_schema_standards.py`
1. Document the new standards in this README
1. Ensure the test provides actionable feedback for developers

The test suite is designed to be both informative and actionable, providing clear
guidance on what needs to be improved and how to fix issues.
