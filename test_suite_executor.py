from robocop.config import Config
from robocop.executable_test_suite import ExecutableTestSuite

from multiprocessing.pool import Pool
from threading import Thread
from robot.api import logger

from time import sleep

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

