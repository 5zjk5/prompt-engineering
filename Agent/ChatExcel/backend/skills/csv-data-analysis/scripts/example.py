#!/usr/bin/env python3
"""
Example script for the skill.

This script can be called by Claude to perform deterministic operations.
Replace this with your actual skill logic.
"""

import sys
import json

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 example.py <input>")
        sys.exit(1)

    input_data = sys.argv[1]
    # TODO: Add your skill logic here
    result = {"status": "success", "input": input_data}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
