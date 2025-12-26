# Regex Output Matching Example

This example demonstrates how to use regex-based output testing in Testio. This feature is particularly useful when testing output that contains dynamic data such as timestamps, UUIDs, or other variable content.

## Use Case

When testing log messages or other outputs that include timestamps or dynamic data, you often want to verify the message content without requiring an exact match of the timestamp. Regular expressions allow you to define flexible patterns that match the expected output structure while accommodating dynamic values.

## Example Program

The example program (`example_program.py`) generates log messages with timestamps:

```python
"""
Example program that generates log messages with timestamps.
This demonstrates the use case for regex-based testing where
the timestamp is dynamic but the message content needs to be verified.
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
```

## Configuration

The `config.json` file shows how to enable regex matching by setting `"use_regex": true`:

```json
{
	"command": "python3",
	"path": "example_program.py",
	"tests": [
		{
			"input": [],
			"output": [
				"\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\] Application started",
				"\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\] Processing user request",
				"\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\] Request completed successfully"
			],
			"timeout": 5,
			"use_regex": true
		}
	]
}
```

## Key Features

- **Optional Feature**: The `use_regex` field is optional and defaults to `false`, ensuring backward compatibility
- **Full Match**: Regex patterns use `re.fullmatch()` to ensure the entire output matches the pattern
- **Pattern Syntax**: Standard Python regex syntax is supported
- **Error Handling**: Invalid regex patterns are treated as mismatches

## Regex Pattern Explanation

The pattern `\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\]` matches:
- `\\[` and `\\]`: Literal square brackets (escaped in JSON)
- `\\d{4}`: Four digits (year)
- `-`: Literal hyphen
- `\\d{2}`: Two digits (month, day, hour, minute, second)
- Space and colon characters as shown

## Running the Example

```bash
python src/main.py cli examples/regex_output_matching/config.json
```

Expected output:
```
Starting tests for examples/regex_output_matching/example_program.py
Correct tests: 1/1 (100.00%)
#1 Test passed!
```

## More Examples

### Matching Any Number
```json
{
    "output": ["Result: \\d+"],
    "use_regex": true
}
```

### Matching UUIDs
```json
{
    "output": ["Request ID: [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"],
    "use_regex": true
}
```

### Matching with Wildcards
```json
{
    "output": ["Hello, .*!"],
    "use_regex": true
}
```
