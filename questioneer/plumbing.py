from os.path import join
from .metric import from_description
from .survey_types import InterRater

import yaml


def survey_from_config(config, items_path, storage):
    metric = from_description(config['metric'])
    return metric, InterRater(
        config['title'], config['description'], metric, items_path,
        storage)


def survey_from_path(path, storage):
    with open(join(path, 'metric.yaml')) as f:
        cfg = yaml.load(f)
    return survey_from_config(cfg, join(path, 'items'), storage)
