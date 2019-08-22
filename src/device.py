from roborunner.config import Config
import json

class Device(dict):
    def __init__(self, name, local_device=False, **kwargs):
        """
        Acts like a dictionary for a single device. Would be easy to
        add or remove features to make this compatible with desktop
        """
        super().__init__()
        super().update(kwargs)
        super().update({
            'name': name, 
            'local_device': local_device
        })

    def __str__(self):
        return self['name']


class BuildDeviceList:
    def __init__(self, config=None):
        if config is None:
            config = {}
        self.config = Config(**config)

    def build(self):
        if self.config['local_device'] == True:
            return [Device(name='local_device', local_device=True)]
        devices_file = open(self.config['devices_file'], 'r')
        json_devices = json.loads(devices_file.read())['devices']
        return [Device(**json_device) for json_device in json_devices]
