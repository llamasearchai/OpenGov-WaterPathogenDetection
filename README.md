# OpenGov-WaterPathogenDetection

**Comprehensive water pathogen detection and surveillance system for California public health laboratories supporting pathogen monitoring and outbreak detection**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org/downloads/)
[![CI](https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/actions/workflows/ci.yml/badge.svg)](https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/actions/workflows/ci.yml)

OpenGov-WaterPathogenDetection is a production-grade Python system designed to support comprehensive water pathogen detection and surveillance for California public health laboratories. The system integrates AI/ML capabilities with regulatory compliance workflows to support government agencies and organizations in monitoring waterborne pathogens and detecting potential outbreaks.

## Key Features

- **AI-Powered Analysis**: Integrated OpenAI and Ollama support for intelligent pathogen analysis
- **Risk Assessment System**: Real-time pathogen risk assessment with automated alerting and trend analysis
- **Data Export & Reporting**: Multi-format exports (JSON, CSV) with compliance reporting
- **Water Sample Tracking**: Comprehensive sample management with location and pathogen correlation
- **Regulatory Compliance**: Built-in compliance checking and reporting
- **Multi-Provider LLM Support**: Graceful fallback between OpenAI, Ollama, and local models
- **Production-Ready**: Complete with testing, documentation, and deployment tools

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- SQLite 3.8 or higher
- Optional: Ollama for local LLM support

### Install with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/llamasearchai/OpenGov-WaterPathogenDetection.git
cd OpenGov-WaterPathogenDetection

# Create virtual environment and install dependencies
uv venv
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Quick Start

1. **Initialize the database**:
   ```bash
   opengov-waterpathogendetection db init
   opengov-waterpathogendetection db seed
   ```

2. **Start the web interface**:
   ```bash
   opengov-waterpathogendetection serve-datasette
   ```

3. **Run your first analysis**:
   ```bash
   opengov-waterpathogendetection agent run "Analyze pathogen detection data"
   ```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/OpenGov-WaterPathogenDetection.git
cd OpenGov-WaterPathogenDetection

# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run mypy src/

# Format code
uv run black src/
uv run isort src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/issues)
- **Discussions**: [GitHub Discussions](https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/discussions)
- **Email**: nikjois@llamasearch.ai

---

**Built by Nik Jois <nikjois@llamasearch.ai>**
