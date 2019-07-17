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
from robocop.config import Config
from robocop.device import BuildDeviceList
from robocop.executable_test_suite import ExecutableTestSuite, BuildExecutableTestSuites
from robocop.test_suite_executor import TestSuiteExecutor
from robocop.test_suite_tree import TestSuiteTree

from robot.api import ResultWriter, logger

from os import makedirs, path


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
