from asyncio import coroutine
from collections import defaultdict, ChainMap


class InMemory:
    def __init__(self):
        self._active_responses = {}
        self._stored_responses = defaultdict(dict)

    @coroutine
    def get_active_item_id(self, participant_id):
        return self._active_responses.get(participant_id)

    @coroutine
    def set_active_item_id(self, participant_id, active_item_id):
        if participant_id in self._active_responses:
            raise KeyError('Already an active response for {}'.format(participant_id))
        self._active_responses[participant_id] = active_item_id

    @coroutine
    def store_response(self, participant_id, active_id, model):
        if active_id in self._stored_responses[participant_id]:
            raise KeyError('Already answered that!')
        self._stored_responses[participant_id][active_id] = model
        del self._active_responses[participant_id]

    @coroutine
    def get_answered_item_ids(self, participant_id):
        return frozenset(self._stored_responses[participant_id].keys())

    @coroutine
    def get_raw_results(self):
        columns = []
        response_cols = []
        for p, responses in self._stored_responses.items():
            for i, response in responses.items():
                response = ChainMap(
                    response, {'participant_id': p, 'active_item_id': i})
                if not columns:
                    columns.extend(response.keys())
                response_cols.append([response[c] for c in columns])
        return columns, response_cols
