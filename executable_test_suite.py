from robocop.config import Config
from robocop.device import Device, BuildDeviceList

from robot.api import TestCaseFile, TestSuiteBuilder, logger

from os import path, makedirs, listdir

class ExecutableTestSuite(Device):

    def __init__(self, source, config=None, **kwargs):
        if config is None:
            config = {}
        self.source = source
        self.test_name = TestCaseFile(source=self.source).name
        self.config = Config(**config)
        super().__init__(**kwargs)

    def __str__(self):
        return super().__str__()

    @property
    def output(self):
        return str(self) + '.xml'

    @property
    def outputdir(self):
        return path.join(self.config['outputdir'], self.test_name)

    @property
    def variables(self):
        _variables = super().copy()
        _variables['name'] = str(self)
        vars_fmt = []
        for key, value in _variables.items():
            vars_fmt.append(
                '{}:{}'.format(key, value)
            )
        return vars_fmt

    def run(self):
        makedirs(self.outputdir, exist_ok=True)
        stdout = open('{}.out'.format(self.outputdir + '/' + str(self)), 'w')
        stderr = open('{}.err'.format(self.outputdir + '/' + str(self)), 'w')
        suite = TestSuiteBuilder().build(self.source)
        suite.name = str(self)
        if self.config['debug_testcase'] != '':
            suite.filter(included_tests=self.config['debug_testcase'])
        if self.config['max_processes'] == 1 or self.config['debug_testcase'] != '':
            stdout = None
            stderr = None
        results = suite.run(
            variable=self.variables,
            output=path.join(self.test_name, self.output),
            outputdir=self.config['outputdir'],
            loglevel=self.config['loglevel'],
            name=str(self),
            stdout=stdout,
            stderr=stderr
        )
        return results.return_code 


class BuildExecutableTestSuites:
    def __init__(self, config=None):
        if config is None:
            config = {}
        self.config = Config(**config)
        self.test_suites = []

    @staticmethod
    def _build_test_paths(test_paths):
        _final_paths = []
        if not isinstance(test_paths, list):
            test_paths = [test_paths]
        for test_path in test_paths:
            if path.isdir(test_path):
                test_files = listdir(test_path)
                for test_file in filter(lambda x: x.endswith('.robot'), test_files):
                    _final_paths.append(path.join(test_path, test_file))
            else:
                _final_paths.append(test_path)
        return _final_paths

    def build(self, test_paths):
        device_list = BuildDeviceList(self.config).build()
        test_paths = self._build_test_paths(test_paths)
        executables = []
        for device in device_list:
            for test_path in test_paths:
                executables.append(
                    ExecutableTestSuite(source=test_path, config=self.config, **device)
                )
        return executables
