import json
import sys
import subprocess
import multiprocessing
import re

PROGRAM_PATH_JSON = "ProgramPath"
TEST_JSON = "Test\s?\d*"

class ProgramOutput:

	def __init__(self, path, timeout):
		self.path = path
		self.start_program(timeout)
		
	def generate_output(self):
		pipe = subprocess.Popen("python3 {}".format(self.path), 
			shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		communication_result = pipe.communicate()
		assert(len(communication_result) == 2)
		self.stdout = communication_result[0].decode("utf-8") 
		self.stderr = communication_result[1].decode("utf-8") 
		if (pipe.returncode == 0):
			print("stdout: ", self.stdout)

	def start_program(self, timeout):
	    p = multiprocessing.Process(target=self.generate_output)
	    p.start()
	    p.join(timeout)
	    if p.is_alive():
	        p.terminate()

class Parser:
	
	def __init__(self, path):
		self.data = None
		self.read_config_file(path)
		self.validate_config_file()


	def read_config_file(self, path):
		
		try:
			with open(path) as f:
				self.data = json.load(f)

		except EnvironmentError:
			print('Failed to open config file')
	
	def validate_config_file(self):
		if PROGRAM_PATH_JSON not in self.data:
		        raise KeyError('{} not found in config file!'.format(PROGRAM_PATH_JSON))

		flag = False
		for key in self.data:
			flag = re.compile(TEST_JSON).match(key)
			if flag:
				break

		if not flag:
		        raise KeyError('no tests found in config file!')

	

if __name__ == "__main__":

	if len(sys.argv) > 1:
		path = sys.argv[1] 

		parser = Parser(path)
		data = parser.data

		path = data[PROGRAM_PATH_JSON]
		timeout = 1
		ProgramOutput(path, timeout)

