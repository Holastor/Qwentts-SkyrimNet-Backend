#!/usr/bin/env python3
"""
QwenTTS adapter server wrapper for SkyrimNet.
Delegates to the refactored modular implementation in src/main.py.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    from src.main import main
    main()
