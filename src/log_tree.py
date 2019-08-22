from roborunner.config import Config

from robot.api import TestCaseFile, ExecutionResult, ResultWriter, logger
from robot.result.executionresult import Result

from os import path, listdir

class LogTree:
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

    def write(self):
        raise NotImplementedError()

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
        return sorted(_result_paths)


class SuiteLogTree(LogTree):
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
        super().__init__(executable_test_suites, name, config)

    def _create_suite_xml(self, test_name):
        dir_path = path.join(self.config['outputdir'], test_name)
        result = Result()
        result.suite.name = test_name

        result_files = listdir(dir_path)
        result_files = [*filter(lambda result_file: result_file.endswith('.xml'), result_files)]
        result_files = [*map(lambda result_file: path.join(dir_path, result_file), result_files)]
        for result_file in result_files:
            try:
                new_result = ExecutionResult(result_file)
                result.suite.suites.append(new_result.suite)
            except Exception as e:
                logger.info('could not parse result file {}: {}'.format(result_file, e))
        result.save(path.join(self.config['outputdir'], test_name + '.xml'))

    def _create_suite_xmls(self):
        for name in self.test_names:
            self._create_suite_xml(name)

    def _combine_suite_xmls(self):
        result = Result()
        result.suite.name = self.name
        for result_path in self.result_paths:
            new_result = ExecutionResult(result_path)
            result.suite.suites.append(new_result.suite)
        result.save(path=path.join(self.config['outputdir'], 'output.xml'))

    def write(self):
        self._create_suite_xmls()
        self._combine_suite_xmls()
        writer = ResultWriter(path.join(self.config['outputdir'], 'output.xml'))
        writer.write_results(
            suitestatlevel=self.config['suite_stat_level'],
            outputdir=self.config['outputdir'],
        )

class DeviceLogTree(LogTree):

    def __init__(self, executable_test_suites, name, config=None):
        super().__init__(executable_test_suites, name, config)
        self._device_filenames = None
    
    @property
    def device_filenames(self):
        if self._device_filenames:
            return self._device_filenames
        dir_path = path.join(self.config['outputdir'], self.test_names[0])
        result_files = listdir(dir_path)
        device_xml_files = [*filter(lambda result_file: result_file.endswith('.xml'), result_files)]
        self._device_filenames = sorted(device_xml_files)
        return self._device_filenames
    
    def _gather_device_xmls(self):
        for device_file in self.device_filenames:
            device_result = Result()
            device_result.name = device_file.replace('.xml', '')
            for test_name in self.test_names:
                current_result_path = path.join(self.config['outputdir'], test_name, device_file)
                try:
                    current_result = ExecutionResult(current_result_path)
                    current_result.suite.name = test_name
                    device_result.suite.suites.append(current_result.suite)
                except Exception as e:
                    logger.error('unable to parse log file {}: {}'.format(current_result_path, e))
            device_result.save(path=path.join(self.config['outputdir'], device_file))
    
    def _combine_all_devices(self):
        all_devices = Result()
        all_devices.suite.name = self.name

        for device_file in self.device_filenames:
            current_result = ExecutionResult(path.join(self.config['outputdir'], device_file))
            current_result.suite.name = device_file
            all_devices.suite.suites.append(current_result.suite)
        all_devices.save(path=path.join(self.config['outputdir'], 'devices.xml'))

    def write(self):
        self._gather_device_xmls()
        self._combine_all_devices()
        writer = ResultWriter(path.join(self.config['outputdir'], 'devices.xml'))
        writer.write_results(
            suitestatlevel=self.config['suite_stat_level'],
            outputdir=self.config['outputdir'],
            log='devices.html',
            report=None
        )

