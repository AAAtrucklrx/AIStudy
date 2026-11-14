"""Validate authored CH05-09 lessons against the immutable textbook and reader."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DELIVERY=ROOT.parent/'delivery/复变函数-交互有声版-20261028'
SOURCE=ROOT/'data/parse/complex-analysis-v2'
TARGET=Path(__file__).with_name('lessons-CH05-09.json')
chapters=json.loads((SOURCE/'chapters.json').read_text())
expected={u['unit_id']:u for u in chapters['lesson_units'] if 5<=int(u['unit_id'][2:4])<=9}
s=(DELIVERY/'book/data/data.js').read_text(); old=json.loads(s[s.index('=')+1:].strip().rstrip(';'))
assert TARGET.exists(), 'authored lesson file missing (expected initial failure)'
data=json.loads(TARGET.read_text()); assert data['schema_version']=='TextbookLessonRevisionV1'
assert set(data['units'])<=set(expected)
if '--partial' not in sys.argv: assert set(data['units'])==set(expected),(len(data['units']),len(expected))
for uid,u in data['units'].items():
 assert u['unit_id']==uid and u['title'] and u['next_bridge']
 assert u['source_path']==expected[uid]['original_text'] and (SOURCE/u['source_path']).exists()
 body=u['body_markdown']; assert len(body)>250,(uid,'too short')
 anchors={b['anchor'] for b in old['units'][uid]['reader_document']['blocks']}
 for a in re.findall(r'\]\(#(reader-[a-f0-9]+)\)',body): assert a in anchors,(uid,a)
 assert '@EX:' not in body
 declared=[]
 for kind,key in [('VISUAL','visuals'),('MEDIA','media')]:
  for v in u[key]:
   marker=f'[[TEACHING_{kind}:{v["id"]}]]';assert v['marker']==marker and body.count(marker)==1,(uid,marker)
   assert len(body.split(marker)[0].strip())>35 and len(body.split(marker)[1].strip())>35,(uid,'orphan media')
   declared.append(marker)
   if kind=='VISUAL':
    assert all(v.get(k) for k in ['kind','model_title','title','purpose','action','observation','conclusion','formula'])
   else:
    assert v['request_id'] in {a['request_id'] for a in old['animations'].get(uid,[])},(uid,v['request_id'])
    original=next(a for a in old['animations'][uid] if a['request_id']==v['request_id'])
    assert [s['step_id'] for s in v['narration_steps']]==[s['step_id'] for s in original['steps']],(uid,'media steps differ from source')
 assert set(re.findall(r'\[\[TEACHING_(?:VISUAL|MEDIA):[^\]]+\]\]',body))==set(declared)
print(f'PASS {len(data["units"])} / {len(expected)} lessons; sources, anchors, markers, media references valid')
