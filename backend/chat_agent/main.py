#!/usr/bin/env python3
"""
Chat Agent Command Line Interface
Usage:
    python main.py init --chat_id <chat_id> --user_id <user_id> [--server_url <url>]
    python main.py send_message --chat_id <chat_id> --user_id <user_id> --message <message> [--server_url <url>]
    python main.py call_tool --chat_id <chat_id> --user_id <user_id> --tool_call_id <tool_call_id> --tool_name <tool_name> --tool_params <json_params> [--server_url <url>]
    python main.py call_tool_feedback --chat_id <chat_id> --user_id <user_id> --chat_sub_task_id <sub_task_id> --output_path <output_file> [--server_url <url>]
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
    from chat_agent import ChatAgent
except ImportError:
    # Fallback for when running from different directory
    from .chat_agent import ChatAgent


def main():
    parser = argparse.ArgumentParser(description='Chat Agent CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize chat agent')
    init_parser.add_argument('--chat_id', required=True, help='Chat ID')
    init_parser.add_argument('--user_id', required=True, help='User ID')
    init_parser.add_argument('--server_url', default='http://localhost:5000', help='Server URL')
    
    # Send message command
    send_parser = subparsers.add_parser('send_message', help='Send message to chat')
    send_parser.add_argument('--chat_id', required=True, help='Chat ID')
    send_parser.add_argument('--user_id', required=True, help='User ID')
    send_parser.add_argument('--message', required=True, help='Message content')
    send_parser.add_argument('--attached_files', help='Attached files s3 path as JSON string')
    send_parser.add_argument('--server_url', default='http://localhost:5000', help='Server URL')
    
    # Call tool command
    tool_parser = subparsers.add_parser('call_tool', help='Call a tool')
    tool_parser.add_argument('--chat_id', required=True, help='Chat ID')
    tool_parser.add_argument('--tool_call_id', required=True, help='Tool Call ID')
    tool_parser.add_argument('--user_id', required=True, help='User ID')
    tool_parser.add_argument('--tool_name', required=True, help='Tool name')
    tool_parser.add_argument('--tool_params', default='{}', help='Tool parameters as JSON string')
    tool_parser.add_argument('--server_url', default='http://localhost:5000', help='Server URL')
    
    # Call tool feedback command
    feedback_parser = subparsers.add_parser('call_tool_feedback', help='Process tool feedback')
    feedback_parser.add_argument('--chat_id', required=True, help='Chat ID')
    feedback_parser.add_argument('--user_id', required=True, help='User ID')
    feedback_parser.add_argument('--chat_sub_task_id', required=True, help='Sub task ID')
    feedback_parser.add_argument('--output_path', required=True, help='Tool output file path')
    feedback_parser.add_argument('--server_url', default='http://localhost:5000', help='Server URL')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'init':
            chat_agent = ChatAgent(args.chat_id, user_id=args.user_id)
            result = chat_agent.init()
            if result:
                print(json.dumps({"status": "success", "message": "Chat agent initialized"}))
            else:
                print(json.dumps({"status": "error", "message": "Failed to initialize chat agent"}))
                sys.exit(1)
                
        elif args.command == 'send_message':
            attached_files = []
            if args.attached_files:
                try:
                    attached_files = json.loads(args.attached_files)
                except json.JSONDecodeError:
                    print(json.dumps({"status": "error", "message": "Invalid attached_files JSON"}))
                    sys.exit(1)
            
            chat_agent = ChatAgent(args.chat_id, user_id=args.user_id)
            result = chat_agent.send_message(args.message, attached_files=attached_files)
            if result:
                print(json.dumps({"status": "success", "message": "Message sent successfully"}))
            else:
                print(json.dumps({"status": "error", "message": "Failed to send message"}))
                sys.exit(1)
                
        elif args.command == 'call_tool':
            try:
                tool_params = json.loads(args.tool_params)
            except json.JSONDecodeError:
                print(json.dumps({"status": "error", "message": "Invalid tool_params JSON"}))
                sys.exit(1)

            chat_agent = ChatAgent(args.chat_id, user_id=args.user_id)
            result = chat_agent.call_tool(args.tool_name, tool_params, tool_call_id=args.tool_call_id)
            print(json.dumps(result))
            
        elif args.command == 'call_tool_feedback':
            chat_agent = ChatAgent(args.chat_id, user_id=args.user_id)
            if not os.path.isfile(args.output_path):
                print(json.dumps({"status": "error", "message": f"Output file {args.output_path} does not exist"}))
                sys.exit(1)
            with open(args.output_path, 'r') as f:
                output = f.read()
            result = chat_agent.call_tool_feedback(args.chat_sub_task_id, output)
            if result:
                print(json.dumps({"status": "success", "message": "Tool feedback processed"}))
            else:
                print(json.dumps({"status": "error", "message": "Failed to process tool feedback"}))
                sys.exit(1)
                
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()