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
from roborunner.config import Config
from roborunner.device import BuildDeviceList
from roborunner.executable_test_suite import ExecutableTestSuite, BuildExecutableTestSuites
from roborunner.test_suite_executor import TestSuiteExecutor
from roborunner.log_tree import DeviceLogTree, SuiteLogTree

from robot.api import ResultWriter, logger

from os import makedirs, path
import json
import sys

def log_config(config):
    logger.info(
        'Running tests with configuration: {}'.format(json.dumps(config, indent=4, sort_keys=True)),
        also_console=True
    )

def log_devices(devices):
    devices_fmt = ''
    for device in devices:
        devices_fmt += '\n{}'.format(json.dumps(device, indent=4, sort_keys=True))
    logger.info(
        'Running tests on the following devices:{}'.format(devices_fmt),
        also_console=True
    )


def run(args=None):
    if not args:
        args = sys.argv[1:]
    config = Config.parse_args(args)
    if not path.exists(config['devices_file']) and not config['local_device']:
        print('devices file {} does not exist'.format(config['devices_file']))
        sys.exit(1)
    log_config(config)
    makedirs(config['outputdir'], exist_ok=True)
    devices = BuildDeviceList(config=config).build()
    log_devices(devices)
    executables = BuildExecutableTestSuites(devices=devices, config=config).build()
    t = TestSuiteExecutor(executables, config=config)
    t.run()
    tree = SuiteLogTree(executables, name=config['top_level_name'], config=config)
    tree.write()
    tree = DeviceLogTree(executables, name=config['top_level_name'], config=config)
    tree.write()
