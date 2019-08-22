import argparse
from robot.api import logger

from os import cpu_count


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
            '--max-processes',
            type=int,
            dest='max_processes',
            help='set the maximum number of processes, \
                defaults to 4 or twice your cpu count. Whichever is higher.',
            default=max(4, cpu_count() * 2)
        )
        parser.add_argument(
            '--local',
            action='store_true',
            dest='local_device',
            help='Run the test on the local machine or a device connected to the local machine',
            default=False
        )
        parser.add_argument(
            '--top-level-name',
            type=str,
            dest='top_level_name',
            help='Set the top level name for the log and report files',
            default='MoWeb Smoke Tests'
        )
        parser.add_argument(
            '--suite-stat-level',
            type=str,
            dest='suite_stat_level',
            default=3
        )
        parser.add_argument(
            '--test',
            type=str,
            default=None,
            dest='debug_testcase',
            help='Select test cases to run by name or long name. Name\
                 is case and space insensitive and it can also be a\
                 simple pattern where `*` matches anything and `?`\
                 matches any char.'
        )
        parser.add_argument(
            '--devices',
            type=str,
            dest='devices_file',
            help='set the json file containing a list of devices',
            default='devices.json'
        )
        parser.add_argument(
            '--rerun-failed',
            action='store_true',
            dest='rerun_failed',
            help='Set whether to rerun test suites with failed test cases. Defaults to True',
            default=False
        )
        parser.add_argument(
            '--outputdir',
            type=str,
            help='directory to output test results',
            default='results'
        )
        parser.add_argument(
            '--include',
            dest='include_tags',
            type=str,
            help='only run these tests with this tag. Accepts * and ? as well.',
            default=None
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
