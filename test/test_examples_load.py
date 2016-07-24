from asyncio import get_event_loop
from os.path import dirname, join
from os import listdir, pardir
from html.parser import HTMLParser

import pytest

from questioneer.plumbing import survey_from_path
from questioneer.persistence import InMemory

_module_base = join(dirname(__file__), pardir)
_examples_path = join(_module_base, 'examples')

loop = get_event_loop()


def _check_valid_html(text):
    p = HTMLParser()
    p.feed(text)
    p.close()


@pytest.mark.parametrize(
    'example_path',
    (join(_examples_path, e) for e in listdir(_examples_path)))
def test_example_loads(example_path):
    storage = InMemory()
    metric, survey = survey_from_path(example_path, storage)
    index_text = loop.run_until_complete(survey.get_index(lambda _: ''))
    _check_valid_html(index_text)
    item_text = loop.run_until_complete(survey.get_item('someone'))
    _check_valid_html(item_text)
