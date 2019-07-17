"""

7/11/2019  Nicholas Grout

This script allows for three things:
1) Running the same suites with multiple parameters
2) Running multiple robot tests in parallel
3) Combining many log files in a human readable format

We use several classes to abstract out tasks and make this
happen. We also rely heavily on the robot framework
Python api, which can be found here:

> https://robot-framework.readthedocs.io


"""
from robot.api import TestSuiteBuilder, ResultWriter, ExecutionResult, logger

from robot.result.executionresult import Result

import argparse
from os import path, makedirs, cpu_count, listdir
from time import sleep
from csv import DictReader
from sys import argv

from robot.api import TestCaseFile
from multiprocessing.pool import Pool
from threading import Thread


class Device(dict):
    def __init__(self, os_type, device, os_version, browser, local_device=False):
        """
        Acts like a dictionary for a single device. Would be easy to
        add or remove features to make this compatible with desktop

        :param os_type:
        :param device:
        :param os_version:
        :param browser:
        :param local_device:
        """
        super().__init__()
        super().update({
            'local_device': local_device,
            'os_type': os_type,
            'device': device,
            'os_version': os_version,
            'browser': browser,
        })

    def __str__(self):
        """

        :return:
        """
        if self['local_device']:
            return 'local_device'
        return '{}-{}-{}-{}'.format(
            self['os_type'],
            self['device'],
            self['os_version'],
            self['browser'],
        )


class Config(dict):

    @staticmethod
    def parse_args(args):
        """
        Allows us to parse arguments.
        Use --help to see a full list of options

        :param args:
        :return: Config object with parsed out arguments (or default values)
        """
        parser = argparse.ArgumentParser(description='Set configuration for run.py')
        parser.add_argument(
            '--loglevel',
            help='set the loglevel accoring to RF\'s log config',
            default='DEBUG',
            type=str
        )
        parser.add_argument(
            '--suite_stat_level',
            help='set the suite_stat_level. This is currently broken',
            default=2,
            type=int
        )
        parser.add_argument(
            '--max_processes',
            type=int,
            help='set the maximum number of processes, \
                defaults to 6 or twice your cpu count. Whichever is higher',
            default=max(6, cpu_count() * 2)
        )
        parser.add_argument(
            '--local_device',
            action='store_true',
            help='Run the test on an Android device attached to the local machine',
            default=False
        )
        parser.add_argument(
            '--top_level_name',
            type=str,
            help='Set the top level name for the log and report files',
            default='MoWeb Smoke Tests'
        )
        parser.add_argument(
            '--debug_testcase',
            type=str,
            default='',
            help='Specify the test case you want to run'
        )
        parser.add_argument(
            '--run_config_file',
            type=str,
            help='set the config file with a list of devices',
            default='run_configs.csv'
        )
        parser.add_argument(
            '--outputdir',
            type=str,
            help='directory to output test results',
            default='Results'
        )
        parser.add_argument(
            'test_file_paths',
            nargs='*',
            default=['tests/'],
            help='Specify the test files which will be run'
        )
        try:
            parsed_args = parser.parse_args(args)
            dict_args = vars(parsed_args)
            if dict_args['local_device']:
                dict_args['max_processes'] = 1
            return dict_args
        except Exception as e:
            logger.error(str(e))
            raise e

    def __init__(self, *args, **kwargs):
        """

        :param kwargs: a set of options which the config object will copy into itself
        """
        self.update(Config.parse_args(args))
        super().__init__(**kwargs)


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


class TestSuiteExecutor(Pool):

    @staticmethod
    def _error_callback(err):
        logger.error('executing test suite failed: {}'.format(err))
        raise err

    def __init__(self, ex_test_suites, config={}):
        if not isinstance(ex_test_suites, list):
            if isinstance(ex_test_suites[0], ExecutableTestSuite):
                raise TypeError('ex_test_suites must be of type {}'.format(type(ExecutableTestSuite)))
        self.config = Config(**config)
        self.suites = ex_test_suites
        self.processes = []
        super().__init__(processes=self.config['max_processes'])

    def _log_update(self):
        sleep(0.1)
        progress = 0
        last_progress = -1
        while progress < len(self.suites):
            progress = 0
            for process, suite in self.processes:
                if process.ready():
                    progress += 1
            if last_progress != progress:
                for process, suite in self.processes:
                    statuses = {True: 'FINISHED    ', False: 'NOT FINISHED'}
                    logger.info('{}\t{} on {}'.format(statuses[process.ready()], suite.test_name, str(suite)),
                                also_console=True)
                logger.info(
                    'tests finished: {}/{}\n'.format(
                        progress, len(self.suites)
                    ),
                    also_console=True
                )
            sleep(0.1)
            last_progress = progress

    def run(self):
        logger.info('starting execution of {} test suites on up to {} processes'
                    .format(len(self.suites), self.config['max_processes']), also_console=True)
        log_thread = Thread(name='log_update_thread', target=TestSuiteExecutor._log_update, args=(self,))
        log_thread.start()
        for suite in self.suites:
            new_process = super().apply_async(
                ExecutableTestSuite.run,
                args=(suite,),
                error_callback=TestSuiteExecutor._error_callback
            )
            self.processes.append((new_process, suite))
        super().close()
        super().join()
        log_thread.join()


class TestSuiteTree:
    # we want this structure for the log file:
    #        top level
    #     /    /     \     \
    #   suite suite suite  suite
    #   /  \   /  \  /  \  /   \
    # d    d   d  d d   d d    d
    #
    # where d is a test suite with a device configuration,
    # and the lists of suites and devices are variable length
    """
    This class aggregates all the log files into a readable tree. This is one
    of the main problems with using multiple robot tests in parallel, is combining
    log files after execution. This class aims to make a clear, hierarchy of logs
    and suites.
    """

    def __init__(self, executable_test_suites, name, config=None):
        """

        :param executable_test_suites:
        :param name:
        :param config:
        """
        if config is None:
            config = {}
        self._test_paths = list({*map(lambda x: x.source, executable_test_suites)})
        self.name = name
        self.config = Config(**config)

    @property
    def test_names(self):
        test_names = []
        for test_path in self._test_paths:
            test_names.append(TestCaseFile(source=test_path).name)
        return test_names

    @property
    def result_paths(self):
        _result_paths = []
        for test_name in self.test_names:
            _result_paths.append(
                path.join(
                    self.config['outputdir'],
                    test_name + '.xml'
                )
            )
        return _result_paths

    def _create_suite_xml(self, test_name):
        dir_path = path.join(self.config['outputdir'], test_name)
        result = Result()
        result.suite.name = test_name

        result_files = listdir(dir_path)
        result_files = [*filter(lambda result_file: result_file.endswith('.xml'), result_files)]
        result_files = [*map(lambda result_file: path.join(dir_path, result_file), result_files)]
        for result_file in result_files:
            new_result = ExecutionResult(result_file)
            result.suite.suites.append(new_result.suite)
        result.configure(stat_config={'suite_stat_level': self.config['suite_stat_level']})
        result.save(path.join(self.config['outputdir'], test_name + '.xml'))

    def _create_suite_xmls(self):
        for name in self.test_names:
            try:
                self._create_suite_xml(name)
            except Exception as e:
                logger.error(
                    'could not combine xml files for test suite {}: {}'
                        .format(name, e))
                raise e

    def _combine_suite_xmls(self):
        result = Result()
        result.suite.name = self.name
        for result_path in self.result_paths:
            new_result = ExecutionResult(result_path)
            result.suite.suites.append(new_result.suite)
        result.configure(stat_config={'suite_stat_level': self.config['suite_stat_level']})
        result.save(path=path.join(self.config['outputdir'], 'output.xml'))

    def write(self):
        self._create_suite_xmls()
        self._combine_suite_xmls()
        writer = ResultWriter(path.join(self.config['outputdir'], 'output.xml'))
        writer.write_results(
            suitestatlevel=self.config['suite_stat_level'],
            outputdir=self.config['outputdir'],
        )


class BuildDeviceList:
    def __init__(self, config=None):
        if config is None:
            config = {}
        self.devices = []
        self.config = Config(**config)

    def build(self):
        if self.config['local_device'] == True:
            return [Device('', '', '', '', local_device=True)]
        config_file = open(self.config['run_config_file'], 'r')
        reader = DictReader(config_file, delimiter=',')
        for row in reader:
            self.devices.append(Device(**row))
        return self.devices


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

def single_test_case(config):
    device = BuildDeviceList(config).build()[0]
    executable = ExecutableTestSuite(source=config['test_file_paths'][0], config=config, **device)
    logger.info(
        'starting "{}" on {}'.format(config['debug_testcase'], device),
        also_console=True
    )
    executable.run()
    writer = ResultWriter(path.join(executable.outputdir, str(executable) + '.xml'))
    writer.write_results(
        outputdir=config['outputdir'],
    )

def run(args):
    makedirs('Results', exist_ok=True)
    config = Config.parse_args(args)
    if config['debug_testcase']:
        single_test_case(config)
        exit(0)
    executables = BuildExecutableTestSuites(config).build(config['test_file_paths'])
    t = TestSuiteExecutor(executables, config=config)
    t.run()
    tree = TestSuiteTree(executables, name=config['top_level_name'])
    tree.write()



if __name__ == '__main__':
    run(argv[1:])

