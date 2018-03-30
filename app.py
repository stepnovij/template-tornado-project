import copy
import json
import logging
from urllib.parse import urlsplit

import tornado
from tornado import gen
import tornado.escape
import tornado.httputil
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler

from settings import app_settings, proxy_path
from storage import Manager
from utils import score_translation, split

LOGGING_FORMAT = '%(asctime)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)

EVALUATE_URL = '/ai/text/evaluate_provider'


class ValidationMixin:
    VALIDATION_STRUCTURE = {
        'context': {
            'data_set_id': 'number',
            'score_type': 'text'
        }
    }

    @classmethod
    def _validate_json(cls, data, validation_structure=None):
        if validation_structure is None:
            validation_structure = cls.VALIDATION_STRUCTURE

        for key in validation_structure.keys():
            try:
                value = data[key]
                if isinstance(value, dict):
                    cls._validate_json(value, validation_structure[key])
            except KeyError as e:
                error_text = 'Not valid data structure, key not found: {}'.format(e.args[0])
                raise tornado.web.HTTPError(400, error_text)

    @classmethod
    def validate_request_payload(cls, request_body):
        try:
            request_payload = tornado.escape.json_decode(request_body)
        except json.decoder.JSONDecodeError:
            raise tornado.web.HTTPError(400)
        cls._validate_json(request_payload)
        return request_payload


class ProxyRequestMixin:

    def _set_header(self, request):
        request.headers = self.request.headers
        request.headers['Host'] = urlsplit(proxy_path[EVALUATE_URL]).netloc

    def create_proxy_request(self, payload_data=None):
        url = proxy_path[EVALUATE_URL]
        req = HTTPRequest(
            url=url,
            method=self.request.method,
            body=tornado.escape.json_encode(payload_data) if payload_data else None,
        )
        self._set_header(req)
        return req


class EvaluateProviderHandler(ProxyRequestMixin, ValidationMixin, RequestHandler):

    def initialize(self, *args, **kwargs):
        self.manager = kwargs.pop('data_store_manager')

    @staticmethod
    def create_payload(data_set, payload_data):
        new_payload = copy.copy(payload_data)
        del new_payload['context']['data_set_id']
        del new_payload['context']['score_type']
        #
        new_payload['context']['to'] = data_set.lang_to

        # new_payload['context']['text'] = data_set.original
        return new_payload

    @staticmethod
    def _get_data_set_id(payload):
        return payload['context']['data_set_id']

    @staticmethod
    def _get_evaluation_type(payload):
        return payload['context']['score_type']

    @staticmethod
    def _evaluate_single(response_data, data_set, evaluation_type):
        evaluation_value = score_translation(
            response_data['results'], data_set.original, evaluation_type
        )
        response_data['score'] = {'type': evaluation_type, 'value': evaluation_value}
        return response_data

    def evaluate(self, response_data, data_set, evaluation_type):
        if isinstance(response_data, list):

            for idx, _ in enumerate(response_data):
                response_data[idx] = self._evaluate_single(
                    response_data[idx],
                    data_set,
                    evaluation_type
                )
            return response_data
        return self._evaluate_single(response_data, data_set, evaluation_type)

    def save_result(self, data_set_id, proxy_response_data):
        self.manager.save(data_set_id, proxy_response_data)

    # No success with Future which is not working with new await, though this was fixed
    # in new version: 5.0.1
    # Used code by @icu0755:
    # https://github.com/tornadoweb/tornado/issues/2276
    @tornado.gen.coroutine
    def get_data_set(self, data_set_id):
        data_set = self.manager.get_data_set(data_set_id)
        return (yield data_set)

    def _split_request_in_multiple(self, data_set, proxy_request_payload):
        threshold = 100
        splited_arrays = split(data_set.original, threshold)
        results_array = [None] * len(splited_arrays)

        proxy_request_payloads = []

        for array in splited_arrays:
            proxy_request_payload['context']['text'] = array
            proxy_request_payloads.append(proxy_request_payload)
        return results_array, proxy_request_payloads

    async def _send_request_gather_response(self, results_array, proxy_request_payloads):
        client = AsyncHTTPClient()
        logging.info('start _send_request_gather_response request %s', self.request)
        waiter = gen.WaitIterator(
            *[client.fetch(self.create_proxy_request(proxy_request_payload))
              for proxy_request_payload in proxy_request_payloads]
        )

        while not waiter.done():
            response = await waiter.next()
            results_array[waiter.current_index] = tornado.escape.json_decode(response.body)

        logging.info('gathering requests %s', self.request)
        final_result = []
        for r in results_array:
            final_result += r['results']

        response_data = results_array[0]
        response_data['results'] = final_result
        logging.info('stop _send_request_gather_response request %s', self.request)
        return response_data

    async def fetch_and_handle(self, proxy_request_payload, data_set):
        results_array, proxy_request_payloads = self._split_request_in_multiple(data_set,
                                                                                proxy_request_payload)

        response_data = await self._send_request_gather_response(results_array,
                                                                 proxy_request_payloads)

        return response_data

    async def post(self, *args, **kwargs):
        logging.info('handle request %s', self.request)
        # validate request:
        request_payload = self.validate_request_payload(self.request.body)
        # get main arguments:
        data_set_id = self._get_data_set_id(request_payload)
        evaluation_type = self._get_evaluation_type(request_payload)
        data_set = await self.get_data_set(data_set_id)

        # create proxy request
        proxy_request_payload = self.create_payload(data_set, request_payload)
        try:
            # client = AsyncHTTPClient()
            # response = await client.fetch(self.create_proxy_request(proxy_request_payload))
            # # get proxy response
            # response_data = tornado.escape.json_decode(response.body)
            logging.info('start fetch_and_handle %s', self.request)
            response_data = await self.fetch_and_handle(proxy_request_payload, data_set)
            logging.info('finish fetch_and_handle %s', self.request)
            # evaluate
            proxy_response_data = self.evaluate(response_data, data_set, evaluation_type)
            # save data_set_id
            self.save_result(data_set_id, proxy_response_data)
            # write response
            self.write(proxy_response_data)
            logging.info('finish handling request %s', self.request)
        except tornado.httpclient.HTTPError as exc:
            self.set_status(500)
            logging.info('exception during request: %s %s', exc.message, self.request)
            self.write(tornado.escape.json_encode({"status": "error", "detail": exc.message}))


class App(Application):
    def __init__(self):
        app_handlers = [
            (EVALUATE_URL, EvaluateProviderHandler, dict(data_store_manager=Manager()))
        ]
        super().__init__(handlers=app_handlers)


if __name__ == '__main__':
    port = app_settings['port']

    if app_settings['env'] == 'dev':
        App().listen(port)

    else:
        server = HTTPServer(App())
        server.bind(port)
        server.start(0)

    IOLoop.current().start()