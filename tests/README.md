# Tests

This directory contains tests for the Liquidation Monitor Bot project.

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=bot --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run Specific Test Files

```bash
# Run only CRUD tests
pytest tests/test_crud.py

# Run only handler tests
pytest tests/test_handlers.py

# Run only schema tests
pytest tests/test_schemas.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_crud.py::TestUserCRUD

# Run a specific test function
pytest tests/test_crud.py::TestUserCRUD::test_create_user
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow
```

### Verbose Output

```bash
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_crud.py` - Tests for CRUD operations (User, LiquidationSettings)
- `test_schemas.py` - Tests for Pydantic schemas validation
- `test_handlers.py` - Tests for Telegram bot handlers
- `test_services.py` - Tests for business logic (liquidation monitoring)

## Test Database

Tests use an in-memory SQLite database for fast execution. Each test gets a fresh database session that is automatically rolled back after the test completes.

## Fixtures

### Database Fixtures

- `test_engine` - Creates a test database engine
- `db_session` - Provides a database session for each test
- `test_user` - Creates a test user in the database
- `test_liquidation_settings` - Creates test liquidation settings

### Data Fixtures

- `sample_user_data` - Sample user data dictionary
- `sample_liquidation_settings_data` - Sample liquidation settings data

## Writing New Tests

1. Import necessary fixtures from `conftest.py`
2. Use `@pytest.mark.asyncio` for async tests
3. Use `@pytest.mark.unit` or `@pytest.mark.integration` to categorize tests
4. Use fixtures for common test data setup

Example:

```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_my_function(db_session: AsyncSession, test_user):
    # Your test code here
    pass
```

