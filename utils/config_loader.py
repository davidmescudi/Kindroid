import yaml

class AppConfig:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    @classmethod
    def load_from_yaml(cls, file_path):
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return cls(**config_data)