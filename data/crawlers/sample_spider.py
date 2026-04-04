#!/usr/bin/env python3
"""
Sample crawler for demonstration purposes.
This crawler simply prints messages and simulates work.
"""

import time
import sys
from datetime import datetime


def main():
    print(f"[{datetime.now().isoformat()}] Starting sample crawler...")
    print(f"[{datetime.now().isoformat()}] Arguments: {sys.argv[1:]}")

    # Simulate some work
    for i in range(5):
        print(f"[{datetime.now().isoformat()}] Processing item {i + 1}/5...")
        time.sleep(1)

    print(f"[{datetime.now().isoformat()}] Crawler completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
