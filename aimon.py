# aimonitor.py
import requests
import os
import json
import time
import sys
import psutil

class Groq:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key.strip()
        # Use the correct Groq API base URL as provided in the original code
        self.base_url = "https://api.groq.com/openai/v1"

    def chat_completions(self, messages, model, temperature=1, max_completion_tokens=1024, top_p=1, stream=False, stop=None):
        """
        Makes a POST request to the Groq API for chat completions, with support for streaming responses.
         List of messages to send to the API.
        The language model to use.
        temperature: Sampling temperature.
        max_completion_tokens: Maximum number of tokens to generate.
        top_p: Controls nucleus sampling.
        stream: Whether to stream responses.
        stop: Stop sequences to end completion.
         The API response (dict) if not streaming, or a generator if streaming.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_completion_tokens,
            "top_p": top_p,
            "stream": stream,
            "stop": stop,
        }

        try:
            response = requests.post(url, headers=headers, json=data, stream=stream)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            if stream:
                # Return the generator for streaming responses
                return response.iter_lines(decode_unicode=True)
            else:
                # Return the JSON response for non-streaming
                return response.json()

        except requests.RequestException as e:
            try:
                # Attempt to get error details from response if available
                error_details = e.response.json() if e.response and e.response.text else {}
                error_message = error_details.get("error", {}).get("message", str(e))
            except:
                 error_message = str(e)
            raise Exception(f"Groq API Error: {error_message}")

# Function to initialize the Groq client
def initialize_client(api_key):
    """
    Initialize and return the Groq client.
    """
    return Groq(api_key)

# Function to send a query to the language model and extract content (for non-streaming)
def get_ai_response_content(client, user_input, model="llama-3.3-70b-versatile", **kwargs):
    """
    Sends a query to the AI and returns the content of the response.
    Assumes non-streaming for this use case.
    """
    if not user_input.strip():
        raise ValueError("Input is required")

    messages = [{"role": "user", "content": user_input}]

    # Ensure stream is False for this function
    kwargs['stream'] = False

    response_json = client.chat_completions(messages=messages, model=model, **kwargs)

    try:
        # Extract the content from the non-streaming JSON response
        return response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        # Print the unexpected response structure for debugging
        print("Unexpected response structure from Groq API:")
        print(json.dumps(response_json, indent=2))
        raise Exception("Malformed response from Groq API")

def analyze_system_data(client, system_info, processes):
    """
    Analyzes system monitoring data using the AI and provides advice.
    """
    print("Sending data to AI for analysis...")
    prompt = "Analyze the following system data and provide concise advice on potential congestion, overload, or malicious activity.\n\n"

    prompt += "System Information:\n"
    for key, value in system_info.items():
        # Format float values for better readability in the prompt
        if isinstance(value, float):
             prompt += f"- {key}: {value:.2f}\n"
        else:
            prompt += f"- {key}: {value}\n"

    prompt += "\nRunning Processes:\n"
    if processes:
        # Limit the number of processes sent to the AI to avoid exceeding token limits

        #  take the top N or filter for high resource users
        processes_for_prompt = sorted(processes, key=lambda p: p.get('cpu_percent', 0), reverse=True)[:20] # Example: top 20 by CPU

        for p in processes_for_prompt:
            # Basic sanitization/formatting for command line to avoid prompt issues
            cmdline_display = p.get('cmdline', 'N/A')
            if len(cmdline_display) > 100: # Truncate long command lines
                cmdline_display = cmdline_display[:97] + "..."
            cmdline_display = cmdline_display.replace('\n', ' ').replace('\r', '') # Remove newlines

            mem_percent = p.get('memory_percent')
            mem_display = f"{mem_percent:.2f}%" if isinstance(mem_percent, float) else "N/A"

            prompt += f"- PID: {p.get('pid', 'N/A')}, Name: {p.get('name', 'N/A')}, User: {p.get('username', 'N/A')}, CPU: {p.get('cpu_percent', 0):.2f}%, Memory: {mem_display}, Cmdline: {cmdline_display}\n"
    else:
        prompt += "No process data available.\n"

    prompt += "\nBased on this data, identify any potential issues (high resource usage, unusual processes, potential malicious indicators) and provide concise, actionable advice. If everything looks normal, state that."

    try:
        # Use the new function that handles content extraction
        advice = get_ai_response_content(client, prompt)
        print("\n--- AI Analysis and Advice ---")
        print(advice)
        print("--- End of AI Analysis ---")
    except Exception as e:
        print(f"Error during AI analysis: {e}")

if __name__ == "__main__":
    # block is for direct testing of aimonitor.py if needed,
    #  primary use case will be being called by system_monitor.py
    groq_api_key = os.environ.get("GROQ_API_KEY")

    if not groq_api_key:
        print("Error: GROQ_API_KEY environment variable not set.")
        print("Please set the GROQ_API_KEY environment variable with your Groq API key.")
        sys.exit(1)

    groq_client = initialize_client(groq_api_key)

    # Example of calling analyze_system_data with dummy data
    print("Running aimonitor.py in standalone test mode...")
    try:
        # Collect actual data for the test run
        print("Collecting system data for test analysis...")
        test_system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_received": psutil.net_io_counters().bytes_recv,
        }
        test_processes = []
        # Collect a sample of processes, maybe filter for high resource users
        all_processes = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                all_processes.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue

        # Sort by CPU and take top N for a more relevant sample for the AI
        test_processes = sorted(all_processes, key=lambda p: p.get('cpu_percent', 0), reverse=True)[:50]

        analyze_system_data(groq_client, test_system_info, test_processes)

    except Exception as e:
        print(f"An error occurred while gathering data or contacting the AI in standalone mode: {e}")