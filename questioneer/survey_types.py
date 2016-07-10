from os import listdir
from os.path import join
from asyncio import coroutine
from uuid import uuid4
import random


html_page_template = '''
<html>
<head>
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>'''


index_body_template = '''
<h1>{title}</h1>
<div>
{description}
</div>
<div>
Explanation of how the survey tool works goes here!
</div>
<a href="participant_url_href">Begin</a>'''


question_body_template = '''
<div>
{item}
</div>
<div>
{form}
</div>'''


class InterRater:
    def __init__(self, title, description, metric, items_dir, persistence):
        self._title = title
        index_body = index_body_template.format(
            title=title, description=description)
        self._index_template = html_page_template.format(
            title=title, body=index_body)
        self._metric = metric
        self._items = self._load_items(items_dir)
        self._all_item_ids = frozenset(self._items.keys())
        self._persistence = persistence

    @staticmethod
    def _load_items(items_dir):
        items = {}
        for item_path in listdir(items_dir):
            with open(join(items_dir, item_path)) as f:
                items[item_path] = f.read()
        return items

    @coroutine
    def get_index(self, get_participant_url):
        participant_id = uuid4()
        return self._index_template.replace(
            'participant_url_href', get_participant_url(participant_id))

    @coroutine
    def _get_item_id(self, participant_id):
        active_id = yield from self._persistence.get_active_item_id(
            participant_id)
        if active_id is None:
            answered_items = yield from (
                self._persistence.get_answered_item_ids(participant_id))
            possible_items = self._all_item_ids - answered_items
            if possible_items:
                active_id = random.choice(tuple(possible_items))
                yield from self._persistence.set_active_item_id(
                    participant_id, active_id)
        return active_id

    @coroutine
    def get_item(self, participant_id):
        item_id = yield from self._get_item_id(participant_id)
        if item_id is not None:
            page_body = question_body_template.format(
                item=self._items[item_id],
                form=self._metric.form_elements)
        else:
            page_body = '<h1>You have responded to all available items.</h1>'
        return html_page_template.format(title=self._title, body=page_body)

    @coroutine
    def store_response(self, participant_id, data):
        active_id = yield from self._persistence.get_active_item_id(
            participant_id)
        if active_id is None:
            raise KeyError('ought to have one')
        yield from self._persistence.store_response(
            participant_id, active_id, self._metric.validate(data))
