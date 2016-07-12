from sys import argv

from .server import run
from .persistence import InMemory
from .plumbing import survey_from_path


storage = InMemory()
run(survey_from_path(argv[1], storage))
