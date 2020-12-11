import json
import sys
import subprocess
import multiprocessing
import re
import os
import errno

PROGRAM_PATH_JSON = "ProgramPath"
TIMEOUT_JSON = "Timeout"
TEST_JSON = "Test\s?\d*"
TEST_INPUT_JSON = "input"
TEST_OUTPUT_JSON = "output"
TEST_PASSED_MSG = "Test passed successfully!"
TEST_FAILED_MSG = "Test failed :("

class ProgramOutput:

	def __init__(self, path, timeout, tests):
		self.path = path
		self.tests = tests
		self.start_program(timeout)
		
	def run_test(self, test):
		pipe = subprocess.Popen("python3 {}".format(self.path), 
			shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		communication_result = pipe.communicate(input=test.input_data)
		assert(len(communication_result) == 2)
		stdout = communication_result[0].decode("utf-8") 
		stderr = communication_result[1].decode("utf-8") 
		if (pipe.returncode == 0):
			self.display_test_result(stdout, stderr, test)
		else:
			pass

	def start_program(self, timeout):
		for test in self.tests:
			p = multiprocessing.Process(target=self.run_test(test))
			p.start()
			p.join(timeout)
			if p.is_alive():
			    p.terminate()

	@staticmethod
	def display_test_result(stdout, stderr, test):

		if stdout == test.input_to_str():
			print(TEST_PASSED_MSG)

		print("Input data: \tExpected:\tResult:")
		print(test.input_to_str(), "\t", test.output_to_str(), "\t", stdout)

		
class Test:

	def __init__(self, input_data, output):
		self.input_data = input_data
		self.output = output

	def input_to_str(self):
		string = ''.join(data for data in self.input_data)
		return string

	def output_to_str(self):
		string = '\n'.join(data for data in self.output)
		return string

class Parser:
	
	def __init__(self, path):
		self.data = None
		self.tests = []
		self.read_config_file(path)
		self.validate_config_file()

	def read_config_file(self, path):
		
		try:
			with open(path) as f:
				self.data = json.load(f)
				self.parse_tests()

		except EnvironmentError:
			print('Failed to open config file')

	def parse_tests(self):
		for key in self.data:
			if re.compile(TEST_JSON).match(key):
				test_data = self.data[key]
				if TEST_INPUT_JSON in test_data and TEST_OUTPUT_JSON in test_data:
					input_data = test_data[TEST_INPUT_JSON]
					output = test_data[TEST_OUTPUT_JSON]
					self.tests.append(Test(input_data, output))
	
	def validate_config_file(self):
		if PROGRAM_PATH_JSON not in self.data:
		        raise KeyError('{} not found in config file!'.format(PROGRAM_PATH_JSON))

		if PROGRAM_PATH_JSON not in self.data:
		        raise KeyError('{} not found in config file!'.format(TIMEOUT_JSON))

		if len(self.tests) == 0:
		        raise KeyError('no tests found in config file!')

def file_exists(path):

	if not os.path.isfile(path):
		raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
	
	return True


def parse_command_line_args(args):
	if len(args) > 1:
		path = args[1]
		if file_exists(path):
			return path
	
	else:
		raise IndexError("You have to provide path to config file as an argument!")   

def main():
	path = parse_command_line_args(sys.argv)
	parser = Parser(path)
	data = parser.data
	path = data[PROGRAM_PATH_JSON]
	timeout = data[TIMEOUT_JSON]
	ProgramOutput(path, timeout, parser.tests)


if __name__ == "__main__":
	main()

