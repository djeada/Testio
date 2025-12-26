# Homework Mode Demo

This example demonstrates the homework assignment mode features of Testio.

## Files

- `config.json` - Test configuration file with 3 test cases
- `alice_perfect.py` - Perfect solution that passes all tests
- `bob_bug.py` - Solution with a bug (wrong multiplication)
- `charlie_incomplete.py` - Incomplete solution (only prints greeting)

## How to Use

### Via Web Interface

1. Start the Testio server:
   ```bash
   python src/main.py fastapi
   ```

2. Navigate to http://localhost:5000/homework

3. Upload the configuration file (`config.json`)

4. Upload the student files (select all three `.py` files)

5. Click "Test All Submissions"

6. View the results for each student with detailed test outcomes

### Via API

You can also test programmatically using the API:

```bash
curl -X POST http://localhost:5000/homework_submission \
  -F "config_file=@config.json" \
  -F "student_files=@alice_perfect.py" \
  -F "student_files=@bob_bug.py" \
  -F "student_files=@charlie_incomplete.py"
```

## Expected Results

- **Alice (alice_perfect.py)**: 100% - All 3 tests pass
- **Bob (bob_bug.py)**: 33.33% - Only 1 test passes (the third test with 0+0 and 0*0)
- **Charlie (charlie_incomplete.py)**: 0% - Fails all tests (missing functionality)

## Test Cases

1. **Test 1**: Input "5" and "3", expects "Hello World", "8" (sum) and "15" (product)
2. **Test 2**: Input "10" and "20", expects "Hello World", "30" (sum) and "200" (product)
3. **Test 3**: Input "0" and "0", expects "Hello World", "0" (sum) and "0" (product)

