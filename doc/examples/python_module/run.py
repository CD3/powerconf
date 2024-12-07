import pathlib

from powerconf import yaml

configs = yaml.powerload(pathlib.Path("CONFIG.yml"))

for config in configs:
    print(config["/simulation/output_file"])
