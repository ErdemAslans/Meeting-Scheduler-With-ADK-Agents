#!/usr/bin/env python3
import os
import sys
import asyncio

# Proje dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    asyncio.run(main())