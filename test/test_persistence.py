import pytest
from contextlib import contextmanager
from asyncio import get_event_loop

from questioneer.persistence import InMemory, SqlLite
from questioneer.metric import Metric, Choice


loop = get_event_loop()

choice = Choice('c', (
    {'name': 'chalk', 'description': 'Soft rock'},
    {'name': 'cheese', 'description': 'Stilton'}))
metric = Metric([choice])


@contextmanager
def in_memory_context():
    yield InMemory()


@contextmanager
def sqlite_context():
    s = SqlLite()
    with s.connection(':memory:', metric):
        yield s


storage_cms = (in_memory_context, sqlite_context)


# Check active item storage
@pytest.mark.parametrize('storage_cm', storage_cms)
def test_active_item(storage_cm):
    with storage_cm() as storage:
        participant_id = 'part-i'
        saii = loop.run_until_complete(
            storage.get_active_item_id(participant_id))
        assert saii is None
        taii = 'some-id'
        loop.run_until_complete(
            storage.set_active_item_id(participant_id, taii))
        saii = loop.run_until_complete(
            storage.get_active_item_id(participant_id))
        assert saii == taii


# Check result storage
@pytest.mark.parametrize('storage_cm', storage_cms)
def test_response_storage(storage_cm):
    with storage_cm() as storage:
        participant_id = 'part-i'
        aiid = 'active-i'
        loop.run_until_complete(
            storage.set_active_item_id(participant_id, aiid))
        response = {'c': choice.options.chalk}
        loop.run_until_complete(
            storage.store_response(participant_id, aiid, response))
        aiid2 = 'active-j'
        loop.run_until_complete(
            storage.set_active_item_id(participant_id, aiid2))
        loop.run_until_complete(
            storage.store_response(participant_id, aiid2, response))
        answered = loop.run_until_complete(
            storage.get_answered_item_ids(participant_id))
        assert answered == frozenset({aiid, aiid2})
