from roborunner.config import Config
from roborunner.executable_test_suite import ExecutableTestSuite

from multiprocessing.pool import Pool
from threading import Thread
from robot.api import logger, TestSuite
from robot.conf import gatherfailed

from time import sleep
from os import path

class TestSuiteExecutor:

    @staticmethod
    def _error_callback(err):
        logger.error('executing test suite failed: {}'.format(err))
        raise err

    def __init__(self, ex_test_suites, config={}):
        if not isinstance(ex_test_suites, list):
            if isinstance(ex_test_suites[0], ExecutableTestSuite):
                raise TypeError('ex_test_suites must be of type {}'.format(type(ExecutableTestSuite)))
        self.config = Config(**config)
        if self.config['local_device']:
            self.config['max_processes'] = 1
        self.suites = ex_test_suites
        self.processes = []
        self.failed_testcases = []
    
    def fmt_update(self, process, suite):
        assert isinstance(suite, ExecutableTestSuite)
        message = '{:<7}\t{test_name} on {device}'
        score = '...'
        if process.ready():
            total = suite.test_count
            passed = str(total - process.get())
            score = '{}/{}'.format(
                passed,
                total
            )
        return message.format(
            score,
            test_name=suite.test_name,
            device=str(suite)
        )

    def _log_update(self):
        progress = 0
        last_progress = -1
        while progress < len(self.suites):
            progress = 0
            for process, suite in self.processes:
                if process.ready():
                    progress += 1
            if last_progress != progress:
                for process, suite in self.processes:
                    logger.info(self.fmt_update(process, suite), also_console=True)
                logger.info(
                    'total test suites finished: {}/{}\n'.format(
                        progress, len(self.suites)
                    ),
                    also_console=True
                )
            last_progress = progress
            sleep(0.1)
    
    def run(self):
        if len(self.suites) <= 1 or self.config['max_processes'] == 1:
            for suite in self.suites:
                suite.run(verbose=True)
            return
        pool = Pool(processes=self.config['max_processes'])
        logger.info('starting execution of {} test suites on up to {} processes'
                    .format(len(self.suites), self.config['max_processes']), also_console=True)
        for suite in self.suites:
            new_process = pool.apply_async(
                ExecutableTestSuite.run,
                args=(suite,),
                error_callback=TestSuiteExecutor._error_callback
            )
            self.processes.append((new_process, suite))
        log_thread = Thread(name='log_update_thread', target=TestSuiteExecutor._log_update, args=(self,))
        log_thread.start()
        pool.close()
        pool.join()
        log_thread.join()
