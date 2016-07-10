from sys import argv

import yaml

from .server import run
from .metric import from_description
from .survey_types import InterRater
from .persistence import InMemory


def survey_from_config(config, storage):
    metric = from_description(config['metric'])
    return InterRater(
        config['title'], config['description'], metric, argv[1] + 'items',
        storage)


storage = InMemory()
with open(argv[1] + 'metric.yaml') as f:
    cfg = yaml.load(f)
run(survey_from_config(cfg, storage))
