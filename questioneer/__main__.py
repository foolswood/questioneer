from sys import argv
from os.path import join

from .server import run
from .persistence import SqlLite
from .persistence import InMemory
from .plumbing import survey_from_path


path = argv[1]
storage = SqlLite()
metric, survey = survey_from_path(path, storage)
with storage.connection(join(path, 'response_db'), metric):
    run(survey)
