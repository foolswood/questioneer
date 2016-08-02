from sqlite3 import connect
from contextlib import contextmanager
import json
from asyncio import coroutine


def table_def(columns, primary_key=None):
    return {'columns': list(columns), 'primary_key': primary_key}


class SqlLite:
    @contextmanager
    def connection(self, path, metric):
        self._init_schema_from_metric(metric)
        self._conn = connect(path)
        try:
            self._init_tables()
            yield
        finally:
            self._conn.close()

    def _init_schema_from_metric(self, metric):
        response_columns = ('participant_id', 'active_item_id')
        response_columns += tuple(q.var for q in metric.questions)
        self.schema = {
            'active_responses': table_def(
                ('participant_id', 'active_item_id'),
                primary_key='participant_id'),
            'responses': table_def(response_columns)
        }

    def _check_existing_schema_matches(self, c):
        c.execute(self._table_creation_sql(
            '_current_schema', ['table_name', 'schema'],
            primary_key='table_name'))
        c.execute('SELECT table_name, schema FROM _current_schema;')
        schema = {name: json.loads(schema) for name, schema in c.fetchall()}
        if schema:
            if schema != self._schema:
                raise RuntimeError('Incompatible db!')

    @staticmethod
    def _table_creation_sql(name, columns, primary_key=None):
        column_defs = []
        if primary_key is None:
            column_defs.append('pk INTEGER PRIMARY KEY AUTOINCREMENT')
        for column in columns:
            s = '{column} VARCHAR'.format(column=column)
            if column == primary_key:
                s += ' PRIMARY KEY'
            column_defs.append(s)
        return 'CREATE TABLE IF NOT EXISTS {name} ({column_defs});'.format(
            name=name, column_defs=', '.join(column_defs))

    def _init_tables(self):
        with self._transaction() as c:
            self._check_existing_schema_matches(c)
            for name, table_def in self.schema.items():
                c.execute(self._table_creation_sql(name, **table_def))

    @contextmanager
    def _transaction(self):
        cursor = self._conn.cursor()
        try:
            yield cursor
        except Exception:
            raise
        else:
            self._conn.commit()

    @coroutine
    def store_response(self, participant_id, active_item_id, response):
        cols = ['participant_id', 'active_item_id']
        vals = [participant_id, active_item_id]
        for c, v in response.items():
            cols.append(c)
            vals.append(v.name)
        with self._transaction() as c:
            c.execute(
                'INSERT INTO responses {cols!r} VALUES {vals!r};'.format(
                    cols=tuple(cols), vals=tuple(vals)))
            c.execute(
                'DELETE FROM active_responses '
                'WHERE participant_id={!r};'.format(
                    participant_id))

    @coroutine
    def get_answered_item_ids(self, participant_id):
        with self._transaction() as c:
            results = c.execute(
                'SELECT active_item_id FROM responses '
                'WHERE participant_id={!r};'.format(participant_id))
            return frozenset(row[0] for row in results.fetchall())

    @coroutine
    def set_active_item_id(self, participant_id, active_item_id):
        with self._transaction() as c:
            c.execute('INSERT INTO active_responses VALUES ({pid!r}, {aiid!r});'.format(
                pid=participant_id, aiid=active_item_id))

    @coroutine
    def get_active_item_id(self, participant_id):
        with self._transaction() as c:
            c.execute(
                'SELECT active_item_id FROM active_responses '
                'WHERE participant_id = {!r};'.format(participant_id))
            row = c.fetchone()
            if row:
                return row[0]

    @coroutine
    def get_raw_results(self):
        cols = tuple(self.schema['responses']['columns'])
        with self._transaction() as c:
            c.execute('SELECT {} from responses;'.format(', '.join(cols)))
            records = c.fetchall()
        return cols, records
