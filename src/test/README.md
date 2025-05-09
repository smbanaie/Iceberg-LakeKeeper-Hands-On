# Banking Reconciliation System Tests

This directory contains tests for the Apache Iceberg Banking Reconciliation System.

## Test Structure

- `python/`: Python test files
  - `test_spark_config.py`: Tests for Spark configuration
  - `test_transaction_model.py`: Tests for the Transaction model
  - `test_matcher.py`: Tests for the transaction matching logic

## Running Tests

You can run the tests using the provided script:

```bash
python scripts/run_tests.py
```

Or from within a Docker container:

```bash
docker exec -it jupyter python /opt/bitnami/spark/scripts/run_tests.py
```

## Writing New Tests

When writing new tests:

1. Create a new file in the `python/` directory with a name starting with `test_`
2. Import the necessary modules and classes
3. Create a test class that inherits from `unittest.TestCase`
4. Implement test methods that start with `test_`
5. Use assertions to verify expected behavior

Example:

```python
import unittest

class TestExample(unittest.TestCase):
    def test_something(self):
        result = 2 + 2
        self.assertEqual(result, 4)
```

## Test Coverage

The tests cover:

- Configuration: Ensuring Spark and Iceberg are properly configured
- Models: Verifying data models work as expected
- ETL: Testing extraction, transformation, and loading of data
- Reconciliation: Testing the matching and reconciliation logic
- API: Testing the REST API endpoints (if implemented)
