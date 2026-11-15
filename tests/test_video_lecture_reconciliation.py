"""Whole-lecture reconciliation contracts; provider calls remain offline here."""
import copy
from types import SimpleNamespace

import pytest


def case():
    lesson = {'sections': [{'id': 'old-1', 'title': 'First', 'start': 0, 'end': 20,
        'markdown': 'Old uncertain term [asr-1]', 'evidence_ids': ['asr-1']}], 'formulas': [], 'uncertainties': []}
    frames = [{'id': 'frame-1', 'start': 30, 'end': 40, 'text': 'later clear text', 'visual_text': 'clear term', 'uncertainties': []}]
    transcript = {'segments': [{'id': 'asr-1', 'start': 0, 'end': 20, 'text': 'uncertain automatic text'}]}
    rewritten = {'sections': [{'id': 'new-1', 'title': 'Full explanation', 'start': 0, 'end': 40,
        'markdown': 'Clear term [frame-1]', 'evidence_ids': ['frame-1', 'asr-1']}], 'formulas': [], 'uncertainties': [],
        'covered_section_ids': ['old-1'], 'corrections': [{'kind': 'replace', 'before': 'Old uncertain term', 'after': 'Clear term',
        'source_ids': ['frame-1'], 'reason': 'Later visual evidence resolves an automatic recognition error', 'start': 0, 'end': 40, 'section_id': 'new-1'}]}
    return lesson, frames, transcript, rewritten


def test_numeric_equivalence_keeps_sign_and_original_sources():
    from aiforstudy.core.video_lecture_reconciliation import numeric_equivalences
    rows = [{'id': 'a', 'layer': 'visual', 'text': r'0.75\times10^{-6}'},
            {'id': 'b', 'layer': 'asr', 'text': '7.5e-7'},
            {'id': 'c', 'layer': 'visual', 'text': r'-7.5\times10^{-7}'}]
    groups = numeric_equivalences(rows)
    assert len(groups) == 1
    assert groups[0]['normalized'] == '7.5E-7'
    assert {x['source_id'] for x in groups[0]['occurrences']} == {'a', 'b'}
    assert groups[0]['occurrences'][0]['text'] == r'0.75\times10^{-6}'


def test_reconciliation_uses_all_windows_without_mutating_raw(tmp_path):
    from aiforstudy.core.video_lecture_reconciliation import reconcile_lecture
    lesson, frames, transcript, rewritten = case()
    originals = copy.deepcopy((lesson, frames, transcript)); captured = []
    def call(role, tag, system, data, validate=None):
        captured.append((role, tag, system, data)); validate(rewritten); return rewritten
    session = SimpleNamespace(call=call, directory=tmp_path, identities=lambda: {'lesson': {'model': 'fixture'}})
    result = reconcile_lecture(session, lesson, frames, transcript, 40, 'revision-a')
    assert (lesson, frames, transcript) == originals
    assert captured[0][3]['frames'][0]['start'] == 30
    assert captured[0][3]['asr'][0]['id'] == 'asr-1'
    assert result['corrections'][0]['before'] == 'Old uncertain term'
    assert result['reconciliation']['semantic_completeness_verified'] is False
    assert (tmp_path / 'revision-a.reconciliation.json').is_file()


@pytest.mark.parametrize('mutation', ['unknown_id', 'wrong_before', 'wrong_after', 'missing_section', 'uncertain_formula', 'time_escape'])
def test_reconciliation_rejects_unbound_edits(mutation):
    from aiforstudy.core.video_lecture_reconciliation import validate_reconciliation
    lesson, frames, transcript, result = case()
    if mutation == 'unknown_id': result['corrections'][0]['source_ids'] = ['imaginary']
    if mutation == 'wrong_before': result['corrections'][0]['before'] = 'not in original'
    if mutation == 'wrong_after': result['corrections'][0]['after'] = 'not in rewritten lesson'
    if mutation == 'missing_section': result['covered_section_ids'] = []
    if mutation == 'uncertain_formula': result['formulas'] = [{'latex': 'x=7', 'source_ids': ['frame-1'], 'uncertainty': 'unclear'}]
    if mutation == 'time_escape': result['corrections'][0]['end'] = 100
    with pytest.raises(ValueError):
        validate_reconciliation(result, lesson, {'frame-1', 'asr-1'}, 40)


def test_re_review_has_independent_tag_and_never_approves(tmp_path):
    from aiforstudy.core.video_lecture_reconciliation import re_review_lecture
    lesson, frames, transcript, rewritten = case(); called = []
    def call(role, tag, system, data, validate=None):
        answer = {'decision': 'no_issues_found', 'issues': [], 'limitations': ['Text evidence only']}
        called.append((role, tag, data)); validate(answer); return answer
    session = SimpleNamespace(call=call, directory=tmp_path)
    review = re_review_lecture(session, rewritten, frames, transcript, 40, 'revision-a')
    assert called[0][0] == 'text_judge'
    assert called[0][1] == 'revision-a-global-review'
    assert review['automatic_approval'] is False
    assert review['reviewed_lesson_digest']
