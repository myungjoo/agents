import requests
import argparse
import sys
import configparser

def get_controller_url():
    """Reads the controller URL from the config file."""
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        host = config.get('Controller', 'host', fallback='127.0.0.1')
        port = config.get('Controller', 'port', fallback='8000')
        return f"http://{host}:{port}"
    except Exception as e:
        print(f"Error reading config.ini: {e}. Defaulting to http://127.0.0.1:8000")
        return "http://127.0.0.1:8000"

BASE_URL = get_controller_url()

def handle_response(response):
    """Helper function to print API responses."""
    if response.status_code >= 200 and response.status_code < 300:
        print("✅ Success:")
        try:
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            print(response.text)
    else:
        print(f"❌ Error ({response.status_code}):")
        try:
            print(response.json())
        except requests.exceptions.JSONDecodeError:
            print(response.text)

def list_agents(args):
    """Lists all available agents and their statuses."""
    print("Fetching agent statuses...")
    try:
        response = requests.get(f"{BASE_URL}/api/agents")
        if response.status_code == 200:
            agents = response.json()
            if not agents:
                print("No agents found or controller not started.")
                return
            print("-" * 40)
            for name, data in agents.items():
                status = data.get('status', 'unknown').upper()
                pid = data.get('pid', 'N/A')
                details = data.get('details', '')
                print(f"AGENT: {name}\n  STATUS: {status}\n  PID: {pid}\n  DETAILS: {details}")
                print("-" * 40)
        else:
            handle_response(response)
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to the Agent Controller at {BASE_URL}.")
        print("   Is the controller.py script running?")

def start_agent(args):
    """Sends a request to start an agent."""
    print(f"Requesting to start agent '{args.agent_name}'...")
    try:
        response = requests.post(f"{BASE_URL}/api/agents/{args.agent_name}/start")
        handle_response(response)
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to the Agent Controller at {BASE_URL}.")

def stop_agent(args):
    """Sends a request to stop an agent."""
    print(f"Requesting to stop agent '{args.agent_name}'...")
    try:
        response = requests.post(f"{BASE_URL}/api/agents/{args.agent_name}/stop")
        handle_response(response)
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to the Agent Controller at {BASE_URL}.")

def status_agent(args):
    """Gets the status of a specific agent."""
    list_agents(None) # Just reuse the list function as it shows all statuses

def run_audit(args):
    """Assigns a code audit job to the code_auditor agent."""
    print(f"Assigning audit job for repo: {args.repo_url}")
    payload = {"agent_name": "code_auditor", "repo_url": args.repo_url}
    try:
        response = requests.post(f"{BASE_URL}/api/jobs/run-audit", json=payload)
        handle_response(response)
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to the Agent Controller at {BASE_URL}.")

def main():
    parser = argparse.ArgumentParser(description="CLI for interacting with the AI Agent System.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'list' command
    parser_list = subparsers.add_parser("list", help="List all available agents and their status.")
    parser_list.set_defaults(func=list_agents)

    # 'start' command
    parser_start = subparsers.add_parser("start", help="Start a specific agent.")
    parser_start.add_argument("agent_name", help="The name of the agent to start.")
    parser_start.set_defaults(func=start_agent)

    # 'stop' command
    parser_stop = subparsers.add_parser("stop", help="Stop a specific agent.")
    parser_stop.add_argument("agent_name", help="The name of the agent to stop.")
    parser_stop.set_defaults(func=stop_agent)
    
    # 'status' command
    parser_status = subparsers.add_parser("status", help="Get the status of all agents.")
    parser_status.set_defaults(func=status_agent)

    # 'run-audit' command
    parser_audit = subparsers.add_parser("run-audit", help="Run a code audit on a GitHub repository.")
    parser_audit.add_argument("--repo_url", required=True, help="The full https URL of the GitHub repository to audit.")
    parser_audit.set_defaults(func=run_audit)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

