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
<h2>How this survey tool works</h2>
<p>
You can score as many reports as you want to.
Do take part even if you only have time to score one report, but the more you score the better.
You don't have to be score all the reports you want to do in one sitting.
If you do some items now and want to do more later the survey can be resumed.
It won't "time out" on you and can be resumed from a different computer.
</p>
<p>
When you click the link below you will be taken to your response page.
Hold onto that page's url: bookmark it, email the link to yourself, write it down or whatever.
Revisiting your response page resumes the survey where you left off.
</p>
</div>
<a href="participant_url_href">Begin</a>'''


question_body_template = '''
<div>
{item}
</div>
<div>
{form}
</div>'''

table_template = '''
<table>
<thead>
<tr>
{headings}
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>'''


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

    @coroutine
    def get_raw_results(self):
        columns, records = yield from self._persistence.get_raw_results()
        headings = ' '.join('<th>{}</th>'.format(c) for c in columns)
        body = '\n</tr>\n<tr>\n'.join(' '.join('<td>{}</td>'.format(d) for d in record) for record in records)
        return table_template.format(headings=headings, rows='<tr>\n{}\n</tr>'.format(body))
