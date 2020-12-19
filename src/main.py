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
TEST_ERROR_MSG = "Your program contains errors :("
TEST_TIMEOUT_MSG = "Your program runs for too long :("


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ProgramOutput:

	def __init__(self, path, timeout, tests, leading_path = None):
		self.path = os.path.join(leading_path, path) if leading_path else path
		self.tests = tests
		self.timeout = timeout
		self.results = []
		self.successful_tests = 0
		self.run()
		
	def run_test(self, test):
		pipe = subprocess.Popen("python3 {}".format(self.path), shell=True, stdout = subprocess.PIPE, 
					stdin=subprocess.PIPE, stderr = subprocess.PIPE)

		communication_result = None

		try:
			communication_result = pipe.communicate(input=test.input_to_str().encode(), 
						timeout=self.timeout)

		except subprocess.TimeoutExpired:
			self.display_timeout_msg()
			return

		assert(len(communication_result) == 2)
		stdout = communication_result[0].decode("utf-8")[:-1]
		stderr = communication_result[1].decode("utf-8") 

		if stdout == test.output_to_str() and not stderr:
			self.successful_tests += 1

		self.results.append((stdout, stderr))

	def run(self):

		for test in self.tests:
			p = multiprocessing.Process(target=self.run_test(test))
			p.start()
			p.join(self.timeout)
			while p.is_alive():
				p.terminate()
				if not p.is_alive():
					ProgramOutput.display_timeout_msg()
		self.display_test_results()

	def display_test_results(self):
		
		print("{}Passed: {}/{} Failed: {}/{}{}".format(bcolors.WARNING, 
			self.successful_tests, len(self.results), 
			len(self.results) - self.successful_tests, 
			len(self.results), bcolors.ENDC))

		assert(len(self.tests) >= len(self.results))

		for test in self.tests:
			stdout, stderr = self.results.pop(0)
			ProgramOutput.display_test_result(stdout, stderr, test)

	@staticmethod
	def display_test_result(stdout, stderr, test):

		if len(stderr) > 0:
			ProgramOutput.display_error_msg(stderr)
			return 

		elif stdout == test.output_to_str():
			print("{}{}".format(bcolors.OKGREEN,TEST_PASSED_MSG))

		else:
			print("{}{}".format(bcolors.FAIL,TEST_FAILED_MSG))

		print("{:<12} {:<12} {:<12}".format("Input data:", "Expected:", "Result:"))
		print("{:<12} {:<12} {:<12}{}".format(test.input_to_str().replace("\n", " "), 
			test.output_to_str().replace("\n", " "), stdout.replace("\n", " "), 
			bcolors.ENDC))

	@staticmethod
	def display_error_msg(stderr):
		print("{}{}{}".format(bcolors.FAIL, TEST_ERROR_MSG, bcolors.ENDC))
		print(stderr)

	@staticmethod
	def display_timeout_msg():
		print("{}{}{}".format(bcolors.WARNING, TEST_TIMEOUT_MSG, bcolors.ENDC))

		
class Test:

	def __init__(self, input_data, output):
		self.input_data = input_data
		self.output = output

	def input_to_str(self):
		if not self.input_data:
			return ''

		string = ''.join(data + '\n' for data in self.input_data)
		return string[:-1]

	def output_to_str(self):
		if not self.output:
			return ''

		string = ''.join(data + '\n' for data in self.output)
		return string[:-1]


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


def get_leading_path(path):
	head, tail = os.path.split(path)
	return head


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
		raise Exception("You have to provide path to config file as an argument!")   


def test_program_output():
	path = parse_command_line_args(sys.argv)
	leading_path = get_leading_path(path)
	parser = Parser(path)
	data = parser.data
	path = data[PROGRAM_PATH_JSON]
	timeout = data[TIMEOUT_JSON]
	ProgramOutput(path, timeout, parser.tests, leading_path)


if __name__ == "__main__":
	test_program_output()
