import pytest
import tornado.escape
import tornado.web

from app import EvaluateProviderHandler, ProxyRequestMixin, ValidationMixin
from tornado.httpclient import HTTPRequest
from urllib.parse import urlsplit


@pytest.fixture
def request_json():
    return {
            "context": {
                "data_set_id": "1",
                "score_type": "bleu"
            },
            "service": {
                "provider": "ai.text.translate.microsoft.translator_text_api.2-0"
            }
        }


@pytest.fixture
def request_body_valid(request_json):
    return tornado.escape.json_encode(request_json)


@pytest.fixture
def request_body_not_valid(request_json):
    json_data = request_json
    json_data['context'].pop('data_set_id')
    return tornado.escape.json_encode(json_data)


@pytest.fixture
def url():
    return 'https://localhost.com/strange_url/1'


@pytest.fixture
def request(url):
    req = HTTPRequest(
        url,
        method='POST',
    )
    req.headers = {'apikey': 'SOMEKEY',
                   'Host': urlsplit(url).netloc}
    return req


def test_validation_mixin__valid_data(request_body_valid, request_json):
    request_payload = ValidationMixin.validate_request_payload(request_body_valid)
    assert request_payload == request_json, request_payload


def test_validation_mixin_not_valid_data(request_body_not_valid):
    with pytest.raises(tornado.web.HTTPError) as excinfo:
        ValidationMixin.validate_request_payload(request_body_not_valid)
    assert 'Not valid data structure' in str(excinfo.value)
    assert 'data_set_id' in str(excinfo.value)
    #
    not_valid_json = '{data}'
    with pytest.raises(tornado.web.HTTPError) as excinfo:
        ValidationMixin.validate_request_payload(not_valid_json)
    assert 'Bad Request' in str(excinfo.value)


def test_proxy_request(request, request_json):
    class Handler:
        def __init__(self, request):
            self.request = request

    class TestingHandler(ProxyRequestMixin, Handler):
        pass
    proxy_req = TestingHandler(request).create_proxy_request(request_json)
    assert proxy_req.headers['Host'] is not None
    assert proxy_req.headers['apikey'] is not None


def test_create_payload(data_set_parsed_from_en_to_ru, request_json):
    new_payload = EvaluateProviderHandler.create_payload(data_set_parsed_from_en_to_ru,
                                                         request_json)
    assert new_payload['context']['to'] == 'ru'
    assert new_payload['service'] is not None

