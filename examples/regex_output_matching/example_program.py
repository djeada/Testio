"""
Example program that generates log messages with timestamps.
This demonstrates the use case for regex-based testing where
the timestamp is dynamic but the message content needs to be verified.

To use this example:
1. Copy this file to 'program.py' in the same directory
2. Run: python src/main.py cli examples/regex_output_matching/config.json
"""
import datetime

def main():
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Print log message with timestamp
    print(f"[{timestamp}] Application started")
    print(f"[{timestamp}] Processing user request")
    print(f"[{timestamp}] Request completed successfully")

if __name__ == "__main__":
    main()
