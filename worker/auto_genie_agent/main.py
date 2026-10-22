#!/usr/bin/env python3
"""
Auto Genie Agent Command Line Interface
Usage:
    python main.py init --generation_id <generation_id> --user_id <user_id>
"""

import sys
import argparse
import json
import os

# Add the parent directory to the path so we can import from server modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# Add current directory to path for relative imports
sys.path.append(os.path.dirname(__file__))

try:
    from auto_genie_agent import AutoGenieAgent
except ImportError:
    # Fallback for when running from different directory
    from .auto_genie_agent import AutoGenieAgent


def main():
    parser = argparse.ArgumentParser(description='Auto Genie Agent CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize auto genie agent')
    init_parser.add_argument('--generation_id', required=True, help='Dynamic Generation ID')
    init_parser.add_argument('--user_id', required=True, help='User ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'init':
            agent = AutoGenieAgent(args.generation_id, user_id=args.user_id)
            result = agent.init()
            if result:
                print(json.dumps({"status": "success", "message": "Auto genie agent initialized"}))
            else:
                print(json.dumps({"status": "error", "message": "Failed to initialize auto genie agent"}))
                sys.exit(1)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
