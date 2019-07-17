from robocop.config import Config
from csv import DictReader

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

