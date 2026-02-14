# JeevanFit Lifestyle Assistant

An AI-powered lifestyle assistant that helps everyday users understand the relationships between their daily habits and body responses.

## Project Structure

```
jeevanfit/
├── __init__.py
├── models/              # Core data models
│   ├── __init__.py
│   └── core.py         # Pydantic models for validation
├── analyzers/          # Analysis components
│   └── __init__.py
├── validators/         # Input validation
│   └── __init__.py
├── privacy/            # Privacy and security
│   └── __init__.py
└── insights/           # Insight generation
    └── __init__.py

tests/
├── __init__.py
├── conftest.py         # Pytest fixtures
└── test_models.py      # Model tests
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=jeevanfit
```

Run only unit tests:
```bash
pytest -m unit
```

Run only property-based tests:
```bash
pytest -m property
```

## Development

This project uses:
- **Pydantic** for data validation
- **pytest** for testing
- **Hypothesis** for property-based testing
- **cryptography** for data encryption

## Core Models

- `LifestyleInput`: Complete user input for a day
- `FoodItem`: Food with nutritional information
- `SleepData`: Sleep quality and duration data
- `BodyType`: User's body type classification
- `Habit`: Daily habits and activities
