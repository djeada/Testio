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

class ProgramOutput:

	def __init__(self, path, timeout, tests):
		self.path = path
		self.tests = tests
		self.start_program(timeout)
		
	def run_tests(self):
		pipe = subprocess.Popen("python3 {}".format(self.path), 
			shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		communication_result = pipe.communicate(input=self.tests[0].input_data)
		assert(len(communication_result) == 2)
		self.stdout = communication_result[0].decode("utf-8") 
		self.stderr = communication_result[1].decode("utf-8") 
		if (pipe.returncode == 0):
			print("stdout: ", self.stdout)
			print("expected: ", self.tests[0].output)

	def start_program(self, timeout):
	    p = multiprocessing.Process(target=self.run_tests)
	    p.start()
	    p.join(timeout)
	    if p.is_alive():
	        p.terminate()

	def display_test_result(self):
		pass

		
class Test:

	def __init__(self, input_data, output):
		self.input_data = input_data
		self.output = output

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
		raise IndexError("You have to provide path to config file as argument!")   

def main():
	path = parse_command_line_args(sys.argv)
	parser = Parser(path)
	data = parser.data
	path = data[PROGRAM_PATH_JSON]
	timeout = data[TIMEOUT_JSON]
	ProgramOutput(path, timeout, parser.tests)


if __name__ == "__main__":
	main()

