"""OpenGov-WaterPathogenDetection - Comprehensive water pathogen detection and surveillance system for California public health laboratories supporting pathogen monitoring and outbreak detection."""

__version__ = "1.0.0"
__author__ = "Nik Jois <nikjois@llamasearch.ai>"
__description__ = "Comprehensive water pathogen detection and surveillance system for California public health laboratories supporting pathogen monitoring and outbreak detection"

from .cli import app

__all__ = ["app"]