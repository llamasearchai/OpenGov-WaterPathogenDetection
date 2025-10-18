# OpenGov-WaterPathogenDetection

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-222%20passing-brightgreen.svg)](https://github.com/llamasearchai/OpenGov-WaterPathogenDetection)
[![Release](https://img.shields.io/badge/release-v1.2.0-blue.svg)](https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/releases/tag/v1.2.0)

OpenGov-WaterPathogenDetection is a production-grade Python system for comprehensive water pathogen detection and surveillance. Designed for California public health laboratories, the system integrates AI/ML capabilities with regulatory compliance workflows to monitor waterborne pathogens and detect potential outbreaks.

## Quick Start

```bash
# Install
git clone https://github.com/llamasearchai/OpenGov-WaterPathogenDetection.git
cd OpenGov-WaterPathogenDetection
uv venv && uv sync && source .venv/bin/activate

# Run complete demo (recommended for first time)
opengov-waterpathogendetection demo

# Start web server
opengov-waterpathogendetection serve
# Visit http://localhost:8000/docs
```

## Key Features

### Professional Tools
- **Batch Sample Import** - Import 1000+ samples from CSV in seconds
- **Automated Compliance** - EPA, CDC, and California Title 22 standards
- **Advanced Analytics** - Outbreak prediction with confidence scoring
- **Notification System** - Multi-channel automated alerts
- **Risk Assessment** - Real-time pathogen risk evaluation
- **Data Export** - Multi-format reports (JSON, CSV)

### Core Capabilities
- **AI-Powered Analysis** - OpenAI and Ollama integration
- **Water Sample Tracking** - Complete lifecycle management
- **Regulatory Compliance** - Built-in compliance checking
- **REST API** - 12 production-ready endpoints
- **CLI Tool** - 10 powerful commands
- **Complete Demo** - One-command demonstration

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Feature List](docs/FEATURES_COMPLETE_v1.2.md) - Complete feature documentation
- [Release Notes](RELEASE_NOTES_v1.2.0.md) - v1.2.0 release details
- [Changelog](CHANGELOG.md) - Version history
- [Contributing](CONTRIBUTING.md) - Contribution guidelines
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server running)

## CLI Commands

```bash
# Demo & Setup
opengov-waterpathogendetection demo              # Complete demonstration
opengov-waterpathogendetection db init           # Initialize database
opengov-waterpathogendetection db seed           # Seed with sample data

# Data Management
opengov-waterpathogendetection import-samples <file.csv>  # Batch import
opengov-waterpathogendetection export --format csv        # Export data

# Analysis & Compliance
opengov-waterpathogendetection risk-assess <type> <conc> <location>
opengov-waterpathogendetection check-compliance <type> <name> <conc>
opengov-waterpathogendetection analyze-trends --days 30

# Server
opengov-waterpathogendetection serve             # Start API server
opengov-waterpathogendetection status            # System status
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=opengovwaterpathogendetection

# Result: 222/222 tests passing (100%)
```

## Production Deployment

### Requirements
- Python 3.11+
- uv or pip
- SQLite 3

### Environment Variables
```bash
# Optional - API Keys for AI features
export OPENAI_API_KEY="your-key-here"

# Optional - Custom configuration
export OPENWATERPATHOGENDETECTION_DEBUG="false"
export OPENWATERPATHOGENDETECTION_DATABASE_URL="sqlite:///data/production.db"
```

### Production Setup
```bash
# Install production dependencies
uv venv && uv sync --no-dev
source .venv/bin/activate

# Initialize database
opengov-waterpathogendetection db init

# Start server
opengov-waterpathogendetection serve --host 0.0.0.0 --port 8000
```

## System Architecture

```
OpenGov-WaterPathogenDetection/
├── src/opengovwaterpathogendetection/
│   ├── cli.py                    # CLI application
│   ├── core/                     # Core functionality
│   │   ├── config.py            # Configuration management
│   │   └── database.py          # Database operations
│   ├── models/                   # Data models
│   │   ├── item.py              # Item models
│   │   └── pathogen.py          # Pathogen models
│   ├── services/                 # Business logic
│   │   ├── agent_service.py     # AI agent service
│   │   ├── analytics.py         # Advanced analytics
│   │   ├── compliance.py        # Compliance checking
│   │   ├── notifications.py     # Alert system
│   │   ├── ollama_service.py    # Local LLM service
│   │   └── risk_assessment.py   # Risk assessment
│   ├── storage/                  # Data storage
│   │   ├── item_storage.py      # Item storage
│   │   ├── pathogen_storage.py  # Pathogen storage
│   │   └── water_sample_storage.py # Sample storage
│   ├── utils/                    # Utilities
│   │   ├── batch_import.py      # CSV import
│   │   ├── demo.py              # Demo system
│   │   ├── export.py            # Data export
│   │   └── logging.py           # Logging
│   └── web/                      # Web API
│       └── app.py               # FastAPI application
├── tests/                        # Test suite (222 tests)
├── docs/                         # Documentation
└── data/                         # Database files
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

**Nik Jois** - Lead Developer  
Email: nikjois@llamasearch.ai  
Organization: LlamaSearch AI

## Links

- **Repository**: https://github.com/llamasearchai/OpenGov-WaterPathogenDetection
- **Issues**: https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/issues
- **Releases**: https://github.com/llamasearchai/OpenGov-WaterPathogenDetection/releases

## Star Us

If you find this project useful, please consider giving it a star on GitHub!

---

Built with care for public health and water quality monitoring
