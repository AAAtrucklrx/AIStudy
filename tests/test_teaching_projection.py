import pytest
from aiforstudy.blocks.content.content_contracts import TeachingEvidenceV1, LessonContentV4, content_digest
from aiforstudy.blocks.content.reader_document import ReaderDocumentV1
from aiforstudy.blocks.content.teaching_projection import compile_teaching_presentation
from aiforstudy.errors import ContractError


def test_evidence_accepts_explicit_role_and_quote():
    row = TeachingEvidenceV1(goal_id='g', purpose='derivation', reader_pointer='/body_markdown', claim_refs=['c'], quote='Proof.', reader_role='proof')
    assert row.reader_role == 'proof'


def test_projection_rejects_stale_document():
    content = {'unit_id': 'u', 'teaching_plan': {'claims': []}, 'teaching_evidence': []}
    reader = ReaderDocumentV1(unit_id='u', content_hash='stale', blocks=[])
    with pytest.raises(ContractError):
        compile_teaching_presentation(content, reader)


def fixture():
    raw = '条件成立时结论成立。\n\n证明：逐步推导。\n\n应用这个结论。'
    content = {'unit_id': 'u', 'teaching_plan': {'claims': [{'id': 'c'}]}, 'teaching_evidence': [
        {'reader_pointer': '/body_markdown', 'claim_refs': ['c'], 'quote': '条件成立时结论成立。', 'reader_role': 'main'},
        {'reader_pointer': '/body_markdown', 'claim_refs': ['c'], 'quote': '证明：逐步推导。', 'reader_role': 'proof'}]}
    reader = ReaderDocumentV1(unit_id='u', content_hash=content_digest(content), blocks=[{'json_pointer':'/body_markdown', 'block_id':'b', 'owner_id':'u', 'raw_text':raw, 'markdown':raw}])
    return content, reader


def test_projection_binds_main_and_optional_to_original_blocks():
    c, r = fixture()
    result = compile_teaching_presentation(c, r)
    assert list(result['roles'].values()) == ['main', 'proof']
    assert result['claim_main_blocks']['c'] == ['b:0']
    assert result['reader_document_hash'] == content_digest(r)


@pytest.mark.parametrize('quote', ['逐步推导', '不存在', '条件成立时结论成立。\n\n证明'])
def test_projection_rejects_missing_or_partial_tokens(quote):
    c, r = fixture()
    c['teaching_evidence'][1]['quote'] = quote
    r._data['content_hash'] = content_digest(c)
    with pytest.raises(ContractError): compile_teaching_presentation(c, r)


def test_projection_rejects_unknown_claim():
    c, r = fixture()
    c['teaching_evidence'][1]['claim_refs'] = ['unknown']
    r._data['content_hash'] = content_digest(c)
    with pytest.raises(ContractError): compile_teaching_presentation(c, r)


def test_duplicate_quote_and_partial_list_are_rejected():
    from aiforstudy.blocks.content.teaching_projection import compile_reader_roles
    for raw, quote in [('重复。\n\n重复。', '重复。'), ('- 一\n- 二', '- 一')]:
        reader = ReaderDocumentV1(blocks=[{'json_pointer':'/body_markdown','block_id':'b','owner_id':'u','raw_text':raw,'markdown':raw}])
        with pytest.raises(ContractError):
            compile_reader_roles(reader, [{'reader_pointer':'/body_markdown','quote':quote,'reader_role':'proof'}])


def test_omitted_role_defaults_to_main():
    c, r = fixture()
    del c['teaching_evidence'][0]['reader_role']
    r._data['content_hash'] = content_digest(c)
    assert compile_teaching_presentation(c, r)['claim_main_blocks']['c'] == ['b:0']
