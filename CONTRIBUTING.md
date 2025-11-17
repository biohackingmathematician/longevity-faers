# Contributing Guidelines

Thank you for your interest in contributing to this project. This document provides guidelines for contributing.

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/biohackingmathematician/longevity-faers.git
cd faers-longevity-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write docstrings for all functions and classes
- Maximum line length: 100 characters

### Formatting

We use `black` for code formatting:

```bash
black src/ scripts/
```

### Linting

We use `flake8` for linting:

```bash
flake8 src/ scripts/
```

## Testing

Run the test suite:

```bash
python test_functionality.py
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure tests pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Maintain professional communication

## Questions

If you have questions, please open an issue on GitHub.
