# A simple calculator that interactively prompts for operations
print("Simple Calculator")
print("Enter first number:")
num1 = float(input())

print("Enter operation (+, -, *, /):")
operation = input()

print("Enter second number:")
num2 = float(input())

if operation == '+':
    result = num1 + num2
elif operation == '-':
    result = num1 - num2
elif operation == '*':
    result = num1 * num2
elif operation == '/':
    if num2 != 0:
        result = num1 / num2
    else:
        print("Error: Division by zero")
        exit(1)
else:
    print("Error: Invalid operation")
    exit(1)

print(f"Result: {result}")
