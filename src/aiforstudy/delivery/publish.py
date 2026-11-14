"""原子发布：**失败不覆盖旧发布**，按清单切换指针。

方案 §10：

> 发布按新 manifest **原子切换 current**，不原地覆盖旧成功版本。单章发布只替换目标章引用，
> 其余已发布产物**字节哈希不变**；全书派生视图可按清单重算。基础版本变更使其他章过期时
> 明确记录 stale，不自动重生成。

方案 §12：

> 默认交付包括章页面目录、目标范围单 HTML、ZIP、manifest 与验收摘要；生产运行自动完成。
> ZIP 从**已验证清单**构建，成员哈希与清单一致。正式包只含阅读所需材料，
> 不带密钥、调试日志或内部临时文件。

## 为什么必须"不原地覆盖"

"就地更新目录"的实现有两个后果，而且都不报错：
① 更新到一半失败 → 交付目录处于**半新半旧**状态，而它看起来是完整的；
② 新版本有问题 → **旧版本已经没了**，连回退对象都不存在。

所以这里只有一种写法：先在**新目录**里把整份 release 建好、验完，最后**原子替换
一个指针文件**（`current.json`）。中途任何一步失败，指针不动，读者看到的仍是上一份合格版本。
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..core.digest import digest_file
from ..core.jsonio import read_json_soft, write_json_atomic
from ..errors import ContractError

CURRENT_NAME = "current.json"
RELEASE_SCHEMA = "1.0"


@dataclass
class ChapterRef:
    chapter_key: str
    release_id: str
    page_digest: str = ""
    parse_revision: str = ""
    context_revision: str = ""

    def as_dict(self) -> dict:
        return {"chapter_key": self.chapter_key, "release_id": self.release_id,
                "page_digest": self.page_digest, "parse_revision": self.parse_revision,
                "context_revision": self.context_revision}


@dataclass
class PublishResult:
    release_id: str
    release_dir: str
    switched: bool
    previous_release: str = ""
    replaced_chapters: tuple[str, ...] = ()
    untouched_chapters: tuple[str, ...] = ()
    member_hashes: dict = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"release_id": self.release_id, "release_dir": self.release_dir,
                "switched": self.switched, "previous_release": self.previous_release,
                "replaced_chapters": list(self.replaced_chapters),
                "untouched_chapters": list(self.untouched_chapters),
                "member_hashes": dict(self.member_hashes), "notes": list(self.notes)}


def _iter_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file())


def member_hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): digest_file(p) for p in _iter_files(root)}


def read_current(releases_root: Path) -> dict:
    return read_json_soft(Path(releases_root) / CURRENT_NAME) or {}


def build_release(releases_root: Path, release_id: str, *, manifest: dict,
                  files: dict[str, bytes], verify_hashes: bool = True) -> tuple[Path, dict]:
    """把一份 release 建在**新目录**里，并逐个核对成员哈希。

    返回 `(release_dir, member_hashes)`。**这一步不碰 current 指针** ——
    建不成、验不过，读者看到的仍是旧版本。
    """
    releases_root = Path(releases_root)
    # ⚠️ 必须先建根目录：`tempfile.mkdtemp(dir=...)` 在父目录不存在时直接抛
    #    FileNotFoundError，而那时调用方看到的是一句"文件找不到"，跟"发布"毫无关系。
    releases_root.mkdir(parents=True, exist_ok=True)
    target = releases_root / release_id
    if target.exists():
        raise ContractError(
            f"release 目录已存在：{target}。发布**不原地覆盖**（方案 §10）——"
            f"不复用旧目录名，请换一个 release_id。")
    staging = Path(tempfile.mkdtemp(prefix=f".{release_id}.", dir=str(releases_root)))
    try:
        for rel, blob in files.items():
            path = staging / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        write_json_atomic(staging / "manifest.json",
                          {"_meta": {"file_type": "release_manifest",
                                     "schema_version": RELEASE_SCHEMA,
                                     "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")},
                           **manifest})
        hashes = member_hashes(staging)
        declared = (manifest.get("members") or {})
        if verify_hashes and declared:
            mismatched = {rel: (declared.get(rel), sha) for rel, sha in hashes.items()
                          if rel in declared and declared[rel] != sha}
            missing = [rel for rel in declared if rel not in hashes]
            if mismatched or missing:
                raise ContractError(
                    f"release 成员与清单不一致：对不上 {list(mismatched)[:3]}｜"
                    f"缺 {missing[:3]}。方案 §12：ZIP 从**已验证清单**构建，"
                    f"成员哈希与清单一致。")
        os.replace(staging, target)      # 原子：要么整份在，要么整份不在
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target, hashes


def switch_current(releases_root: Path, release_id: str, *, book_id: str,
                   scope_kind: str, chapters: tuple[ChapterRef, ...] = ()) -> PublishResult:
    """**原子切换** current 指针。

    单章/多章发布按 `ChapterRef` **只替换目标章**的引用，其余章保持原样
    （方案 §10：其余已发布产物字节哈希不变）。整本发布才整体替换。
    """
    releases_root = Path(releases_root)
    release_dir = releases_root / release_id
    if not release_dir.is_dir():
        raise ContractError(f"release 目录不在位：{release_dir}")
    previous = read_current(releases_root)
    prev_chapters = {row["chapter_key"]: row for row in previous.get("chapters") or []}

    if scope_kind == "book":
        merged = [c.as_dict() for c in chapters]
        replaced = tuple(c.chapter_key for c in chapters)
        untouched = tuple(sorted(set(prev_chapters) - set(replaced)))
    else:
        replaced = tuple(c.chapter_key for c in chapters)
        merged = [c.as_dict() for c in chapters]
        untouched_list: list[str] = []
        for key, row in sorted(prev_chapters.items()):
            if key in replaced:
                continue
            merged.append(row)                       # 其余章的引用原样保留
            untouched_list.append(key)
        merged.sort(key=lambda row: row["chapter_key"])
        untouched = tuple(untouched_list)

    payload = {"_meta": {"file_type": "current_release", "schema_version": RELEASE_SCHEMA,
                         "generator": "aiforstudy.delivery.publish",
                         "field_notes": {
                             "release_id": "当前生效的 release（指针）",
                             "chapters": "按章引用不同范围 release 的产物；每个引用自带 parse/context 版本",
                             "note": "单章发布只替换目标章；其余章字节不变",
                         }},
               "book_id": book_id, "release_id": release_id, "scope_kind": scope_kind,
               "chapters": merged, "switched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    write_json_atomic(releases_root / CURRENT_NAME, payload)
    return PublishResult(release_id=release_id, release_dir=str(release_dir), switched=True,
                         previous_release=str(previous.get("release_id") or ""),
                         replaced_chapters=replaced, untouched_chapters=untouched,
                         member_hashes=member_hashes(release_dir),
                         notes=(f"未替换的章 {len(untouched)} 个，引用保持不变",))


def assert_release_validated(release_dir: Path, *, checks_ok: bool) -> None:
    """发布前的最后一道：**检查没过就不许发布**（§9/§15 A23）。"""
    if not checks_ok:
        raise ContractError(
            f"{release_dir} 的必要检查未通过，**不许发布**。"
            f"方案 §9：正式发布要求所有必要检查 accepted；"
            f"§15 A23：检查非零则包不发布。")


def rollback(releases_root: Path, release_id: str) -> PublishResult:
    """回退：把指针指回上一份**合格的** release（§16）。"""
    releases_root = Path(releases_root)
    release_dir = releases_root / release_id
    if not (release_dir / "manifest.json").is_file():
        raise ContractError(f"回退目标不是一份合格 release：{release_dir}")
    previous = read_current(releases_root)
    payload = {**previous,
               "_meta": {**(previous.get("_meta") or {}),
                         "note": "回退：原子切换指针到上一份合格 release（已发生费用不回滚）"},
               "release_id": release_id,
               "rolled_back_from": previous.get("release_id"),
               "rolled_back_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    write_json_atomic(releases_root / CURRENT_NAME, payload)
    return PublishResult(release_id=release_id, release_dir=str(release_dir), switched=True,
                         previous_release=str(previous.get("release_id") or ""),
                         notes=("回退完成：指针已切回。已发生的服务费用不回滚，"
                                "追加日志保留（方案 §16）",))


__all__ = ["CURRENT_NAME", "RELEASE_SCHEMA", "ChapterRef", "PublishResult", "member_hashes",
           "read_current", "build_release", "switch_current", "assert_release_validated",
           "rollback", "publish_candidate"]


def publish_candidate(*, store, context, scope: tuple[str, ...],
                      scope_kind: str = 'selection', before_switch=None) -> dict:
    """Publish verified HTML after the engine's whole-run quality and budget gates.

    Partial chapter selections have an independent stable namespace, so publishing one
    unit can never replace the complete chapter's current pointer. Same-run resume is
    idempotent only when the immutable release still matches every accepted member.
    """
    from ..contracts.artifact import ArtifactRef
    from ..core.digest import digest_of
    from pathlib import PurePosixPath

    def safe_relative(value: str) -> str:
        rel = PurePosixPath(str(value))
        if not value or rel.is_absolute() or '..' in rel.parts or '\\' in value or ':' in value:
            raise ContractError(f'发布成员必须是安全相对路径：{value!r}')
        return str(rel)

    if not scope or len(scope) != len(set(scope)):
        raise ContractError('发布必须有无重复的已固定范围')
    state = store.node_states().get('delivery')
    if state is None or not state.finished_ok() or state.quality_state.value != 'accepted':
        raise ContractError('缺 accepted delivery 阶段，不能发布')
    artifacts = [ArtifactRef.from_dict(raw).verify() for raw in state.outputs]
    refs = [r for r in artifacts if r.kind == 'delivery.scope' and r.book_id == context.book_id
            and r.producer_stage == 'delivery' and r.path.resolve().is_relative_to(store.work.resolve())]
    if len(refs) != 1:
        raise ContractError('交付范围产物缺失/重复/身份不匹配')
    delivery = (read_json_soft(refs[0].path) or {}).get('payload') or {}
    acceptance = delivery.get('offline_acceptance') or {}
    if acceptance.get('passed') is not True or acceptance.get('blocked') is True:
        raise ContractError('真实浏览器验收未通过，不能发布')
    runtime = [c for c in acceptance.get('checks') or [] if c.get('name') == 'browser-execution']
    if len(runtime) != 1 or runtime[0].get('status') != 'accepted':
        raise ContractError('缺实际浏览器执行证据，不能发布')
    tree = store.work / 'legacy/render'
    members = delivery.get('members') or {}
    if not members:
        raise ContractError('交付资源清单为空')
    files = {}
    for member, expected in members.items():
        rel = safe_relative(member)
        path = tree / rel
        if (not path.resolve().is_relative_to(tree.resolve()) or path.is_symlink()
                or not path.is_file() or digest_file(path) != expected):
            raise ContractError(f'验收后资源改变或缺失：{rel}')
        files[rel] = path.read_bytes()

    chapters = delivery.get('chapters') or []
    if not chapters or len(chapters) != len(set(chapters)):
        raise ContractError('交付章身份缺失/重复')
    rendered_units = []
    for chapter in chapters:
        safe_relative(chapter)
        if f'{chapter}/index.html' not in members:
            raise ContractError(f'交付缺章页面：{chapter}')
        rendered = (read_json_soft(store.work / 'products/render' / f'{chapter}.json') or {}).get('payload') or {}
        rendered_units.extend(rendered.get('units') or [])
    if len(rendered_units) != len(set(rendered_units)) or set(rendered_units) != set(scope):
        raise ContractError('渲染产物没有逐项覆盖发布范围')
    if any(PurePosixPath(name).parts[0] not in chapters for name in members):
        raise ContractError('清单包含范围之外的资源')

    catalog = read_json_soft(Path(context.parse) / 'chapters.json') or {}
    all_chapter_units = {str(row.get('unit_id')) for row in catalog.get('lesson_units') or []
                         if str(row.get('chapter')) in set(chapters)}
    partial = set(scope) != all_chapter_units
    scope_digest = digest_of({'book_id': context.book_id, 'units': sorted(scope)}).split(':')[1][:24]
    releases = Path(context.releases_root)
    if partial:
        releases = releases / 'selections' / scope_digest
    release_id = safe_relative(str(store.run_id))
    if '/' in release_id:
        raise ContractError('release_id 不能带目录')
    manifest = {'book_id': context.book_id, 'release_id': release_id, 'scope': list(scope),
                'scope_kind': scope_kind, 'chapters': chapters, 'members': members,
                'offline_acceptance': acceptance, 'delivery_artifact_digest': refs[0].content_digest,
                'namespace': 'selection' if partial else 'chapters'}
    target = releases / release_id
    if target.exists():
        previous_manifest = read_json_soft(target / 'manifest.json') or {}
        if any(previous_manifest.get(key) != manifest[key] for key in ('book_id', 'scope', 'members')):
            raise ContractError('同run发布目录已存在且内容/范围不同，禁止覆盖')
        for rel, expected in members.items():
            path = target / rel
            if not path.is_file() or path.is_symlink() or digest_file(path) != expected:
                raise ContractError(f'已有发布资源改变：{rel}')
    else:
        target, _ = build_release(releases, release_id, manifest=manifest, files=files)
    assert_release_validated(target, checks_ok=True)
    if before_switch is not None:
        before_switch()
    published = switch_current(releases, release_id, book_id=context.book_id,
        scope_kind='book' if scope_kind == 'all' else 'selection', chapters=tuple(
            ChapterRef(chapter_key=chapter, release_id=release_id,
                page_digest=members[f'{chapter}/index.html'], parse_revision=context.revision)
            for chapter in chapters))
    return {**published.as_dict(), 'pointer': str(releases / CURRENT_NAME),
            'manifest': str(target / 'manifest.json'), 'namespace': manifest['namespace'],
            'scope_digest': scope_digest, 'scope': list(scope), 'formally_published': True}
