import asyncio
from urllib.parse import urljoin, urlencode

from aiohttp import web


class Surveyor:
    def __init__(self, survey):
        self._survey = survey
        self.routes = (
            ('GET', '/', self._get_index),
            ('GET', '/item', self._get_item),
            ('POST', '/item', self._post_response),
            ('GET', '/results/raw', self._get_raw_results),
            ('GET', '/results/summary', self._get_results_summary))

    def _get_participant_url(self, participant_id):
        return '/item?' + urlencode(
            {'participant_id': participant_id})

    @staticmethod
    def _html_response(body, status=200):
        return web.Response(
            status=status, body=body.encode('utf-8'), content_type='text/html')

    @asyncio.coroutine
    def _get_index(self, request):
        body = yield from self._survey.get_index(self._get_participant_url)
        return self._html_response(body)

    @staticmethod
    def _extract_participant_id(request):
        if tuple(request.GET.keys()) != ('participant_id',):
            raise KeyError('FIXME')
        return request.GET['participant_id']

    @asyncio.coroutine
    def _get_item(self, request):
        participant_id = self._extract_participant_id(request)
        body = yield from self._survey.get_item(participant_id)
        return self._html_response(body)

    @asyncio.coroutine
    def _post_response(self, request):
        participant_id = self._extract_participant_id(request)
        data = yield from request.post()
        yield from self._survey.store_response(participant_id, data)
        body = yield from self._survey.get_item(participant_id)
        return self._html_response(body, status=201)

    @asyncio.coroutine
    def _get_raw_results(self, request):
        body = yield from self._survey.get_raw_results()
        return self._html_response(body)

    @asyncio.coroutine
    def _get_results_summary(self, request):
        body = yield from self._survey.get_summary()
        return self._html_response(body)


def run(survey):
    surveyor = Surveyor(survey)
    app = web.Application()
    for route_info in surveyor.routes:
        app.router.add_route(*route_info)
    web.run_app(app)
