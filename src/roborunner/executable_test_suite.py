from roborunner.config import Config
from roborunner.device import Device, BuildDeviceList

from robot.api import TestCaseFile, TestSuiteBuilder, logger
from robot.running import TestSuite

from os import path, makedirs, listdir

class ExecutableTestSuite(Device):

    def __init__(self, source, config=None, **kwargs):
        if config is None:
            config = {}
        self._test_count = None
        self.source = source
        self.test_name = TestCaseFile(source=self.source).name
        self.config = config
        if not self.config:
            self.config = Config()
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
    def test_count(self):
        if self._test_count:
            return self._test_count
        suite = TestSuiteBuilder().build(self.source)
        suite.filter(
            included_tests=self.config['debug_testcase'], 
            included_tags=[self.config['include_tags']]
        )
        self._test_count = suite.test_count
        return self._test_count

    @property
    def variables(self):
        _variables = super().copy()
        _variables['name'] = str(self)
        return ['{}:{}'.format(key, value) for key, value in _variables.items()]

    def run(self, verbose=False):
        makedirs(self.outputdir, exist_ok=True)
        stdout = open('{}.out'.format(self.outputdir + '/' + str(self)), 'w')
        stderr = open('{}.err'.format(self.outputdir + '/' + str(self)), 'w')
        suite = TestSuiteBuilder().build(self.source)
        suite.name = str(self)
        suite.filter(
            included_tests=self.config['debug_testcase'], 
            included_tags=[self.config['include_tags']]
        )
        if verbose:
            stdout = None
            stderr = None
        results = self._run(suite, stdout=stdout, stderr=stderr)
        if self.do_rerun(suite, results):
            logger.console('{} fail rate > 50%, rerunning test'.format(suite.name))
            results = self._run(suite, stdout=stdout, stderr=stderr)
        return results.return_code 
    
    def do_rerun(self, suite, results):
        if suite.test_count == 0:
            return results.return_code
        fail_rate = (results.return_code / float(suite.test_count))
        if self.config.get('rerun_failed') and fail_rate > 0.5:
            return True
        return False
    
    def _run(self, suite, stdout, stderr):
        return suite.run(
            variable=self.variables,
            output=path.join(self.test_name, self.output),
            outputdir=self.config['outputdir'],
            loglevel=self.config['loglevel'],
            name=str(self),
            stdout=stdout,
            stderr=stderr
        )


class BuildExecutableTestSuites:
    def __init__(self, devices=None, config=None):
        if config is None:
            config = {}
        self.config = Config(**config)
        self.test_suites = []
        self.devices = devices
        if not self.devices:
            self.devices = BuildDeviceList(self.config).build()

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

    def build(self):
        if self.config['debug_testcase']:
            test_paths = self.config['test_file_paths']
        else:
            test_paths = self._build_test_paths(self.config['test_file_paths'])
        executables = []
        for test_path in test_paths:
            for device in self.devices:
                executables.append(
                    ExecutableTestSuite(
                        source=test_path, 
                        config=self.config,
                        **device
                    )
                )
        return executables
