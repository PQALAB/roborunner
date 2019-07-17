import argparse
from robot.api import logger


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

