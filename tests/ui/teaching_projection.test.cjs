'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const parser = require('../../blocks/render/assets/reader-markdown.js');
const marked = require('../../blocks/render/vendor/marked.min.js');

test('optional block and its mount stay inside a closed disclosure', () => {
  const raw = '条件成立时结论成立。\n\n证明：逐步推导。\n\n应用这个结论。';
  const field = {block_id:'b', json_pointer:'/body_markdown', owner_id:'u', raw_text:raw};
  const parsed = parser.parseReaderField(raw, {marked, field});
  const proof = parsed.blocks[1];
  const mounts = [{resolved_block_id:proof.block_id, edge:'after', order_at_anchor:0, mount_id:'m'}];
  const html = parser.renderReaderField(parsed, mounts, () => '<div class="reader-media">media</div>', {teachingRoles:{[proof.block_id]:'proof'}, bareMath:false});
  const dom = new JSDOM(html).window.document;
  const details = dom.querySelector('details[data-teaching-role="proof"]');
  assert.ok(details && !details.open);
  assert.match(details.textContent, /逐步推导/);
  assert.ok(details.querySelector('.reader-media'));
  assert.match(dom.body.textContent, /条件成立时结论成立/);
  assert.match(dom.body.textContent, /应用这个结论/);
});

test('Reader layout preserves main conclusion and confines proof media', () => {
  const core = require('../../blocks/render/assets/render-core.js');
  const layout = require('../../blocks/render/assets/reader-layout.js');
  const raw = '## 定理\n\n条件成立时结论成立。\n\n这里是演算。\n\n方法适用于相同条件。';
  const field = {group:'body_markdown',block_id:'b',json_pointer:'/body_markdown',owner_id:'u',raw_text:raw,markdown:raw,field_label:'正文',anchor:'reader-12345678901234567890',collapsed:false};
  const parsed = parser.parseReaderField(raw, {marked,field});
  const proof = parsed.blocks.find(b => raw.slice(b.source_start_cp,b.source_end_cp).includes('演算'));
  const mount = {mount_id:'m',anchor_id:'a',target_pointer:'/body_markdown',resolved_block_id:proof.block_id,edge:'after',order_at_anchor:0,source_id:'v',source_kind:'media',unit_id:'u',source_hash:'x',owner_id:'u'};
  const unit = {title:'测试',reader_document:{schema_version:'ReaderDocumentV1',blocks:[field]},reader_layout:{schema_version:'ReaderLayoutV1',mounts:[mount]},teaching_presentation:{roles:{[proof.block_id]:'proof'}}};
  const renderer = core.createRenderer({marked});renderer.beginUnit({unitId:'u'});
  const dom = new JSDOM('<main>'+renderer.readerDocumentHtml(unit.reader_document,'body',[],unit.reader_layout,unit.teaching_presentation)+'</main>');
  const root = dom.window.document.querySelector('main');layout.enhance(root,unit,'u');
  const detail = root.querySelector('details[data-teaching-role="proof"]');
  assert.ok(detail && !detail.open && detail.querySelector('[data-media-anchor]'));
  assert.ok([...root.querySelectorAll('p')].find(p=>p.textContent.includes('条件成立')).closest('details') === null);
  assert.ok([...root.querySelectorAll('p')].find(p=>p.textContent.includes('方法适用')).closest('details') === null);
  dom.window.close();
});
