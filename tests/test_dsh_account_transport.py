"""Account transport preserves message/image evidence and fails closed locally."""
import base64
from copy import deepcopy
import importlib

import pytest

from aiforstudy.errors import ConfigError


def transport(**kwargs):
    module = importlib.import_module('aiforstudy.providers.dsh_account')
    return module.DshAccountTransport(model='deepseek-flash', **kwargs)


def test_request_keeps_roles_order_and_real_image_bytes(tmp_path):
    image = tmp_path / 'sample.png'
    image.write_bytes(b'controlled-image-bytes')
    messages = [{'role': 'system', 'content': 'Return JSON.'},
                {'role': 'assistant', 'content': '{"prior":true}'},
                {'role': 'user', 'content': 'inspect', 'image_labels': ['frame 1']}]
    before = deepcopy(messages)
    client = transport()
    request = client.request_body(messages=messages, images=[str(image)],
                                  model='deepseek-flash', effort='max', max_tokens=256)
    assert [m['role'] for m in request['messages']] == ['system', 'assistant', 'user']
    parts = request['messages'][-1]['content']
    assert parts[:2] == [{'type': 'text', 'text': 'inspect'}, {'type': 'text', 'text': 'frame 1'}]
    assert base64.b64decode(parts[2]['image_url']['url'].split(',', 1)[1]) == b'controlled-image-bytes'
    assert request['reasoning_effort'] == 'max'
    assert request['max_tokens'] == 256
    assert 'response_format' not in request
    assert messages == before
    assert client.calls == 0


@pytest.mark.parametrize('message', [
    {'role': 'tool', 'content': 'tool output'},
    {'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': 'https://example.org/a.png'}}]},
    {'role': 'user', 'content': [{'type': 'audio', 'data': 'abc'}]},
    {'role': 'assistant', 'content': '', 'tool_calls': [{'name': 'execute'}]},
])
def test_unsupported_inputs_are_refused_before_credentials_or_network(message):
    with pytest.raises(ConfigError):
        transport().request_body(messages=[message])


def test_missing_images_and_label_mismatch_do_not_degrade_to_text(tmp_path):
    client = transport()
    with pytest.raises(ConfigError):
        client.request_body(messages=[{'role': 'user', 'content': 'inspect'}],
                            images=[str(tmp_path / 'missing.png')])
    image = tmp_path / 'sample.png'
    image.write_bytes(b'image')
    with pytest.raises(ConfigError, match='image_labels'):
        client.request_body(messages=[{'role': 'user', 'content': 'inspect', 'image_labels': []}],
                            images=[str(image)])


def test_error_mapping_does_not_expose_provider_messages():
    module = importlib.import_module('aiforstudy.providers.dsh_account')
    with pytest.raises(ConfigError) as caught:
        module.raise_bridge_error({'code': 'ACCOUNT_SIGN_IN_REQUIRED', 'message': 'secret-fixture'})
    assert 'ACCOUNT_SIGN_IN_REQUIRED' in str(caught.value)
    assert 'secret-fixture' not in str(caught.value)


def test_usage_normalization_uses_supplied_provider_counters_only():
    module = importlib.import_module('aiforstudy.providers.dsh_account')
    assert module.normalize_usage({'inputTokens': 23, 'outputTokens': 7,
                                   'cacheReadTokens': 3}) == {
        'prompt_tokens': 26, 'completion_tokens': 7, 'total_tokens': 33,
        'prompt_cache_hit_tokens': 3, 'prompt_cache_miss_tokens': 23,
    }
    assert module.normalize_usage({}) == {}
