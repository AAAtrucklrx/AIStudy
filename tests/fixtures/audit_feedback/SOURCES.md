# S01／S02 审核夹具来源

生成时间：2026-10-07T00:39:11+08:00

来源 run：`data/books/complex-analysis-v2/runs/run-20261006-142529-bad4aa`（**只读**，未写入）

旧判据（`src/aiforstudy/pipeline/transitional.py:_verdict_closed`）：`quote.strip() in current_text`

夹具只保留审核语义相关的字段；上游缓存的 `usage` / `at` / `fingerprint` 已删除，
`quote` / `why` / `status` / 正文**逐字保留**。没有搬入整本书或整章。

## S01 — CH04-S01

* 现象：verdict 判 closed，quote 用『……』拼接多处正文；逐字 `quote in current_text` 失败
* 上游缓存：`work/model-cache/sha256:e8ea8279728c04f550f1c45b7fb2ee20ac75e5cf26914be8da6dcacd54ab6504.json`, `work/model-cache/sha256:d07170e160d278d15522b1d2b0a866a38d37c1f6d46deca49b73c6fda0a2d2e2.json`
* 上游 usage 行：[22, 24]
* current_text：`data/books/complex-analysis-v2/runs/run-20261006-142529-bad4aa/work/legacy/lesson/lessons/CH04-S01.json`（sha256 `3fcf3134170d735d2fe629eb395d1c81c0ef49259a5c95199c5e063c58854a14`，body_markdown sha256 `1e75f084a52afd0301104b3ef48de8a8fbd36e58c852d09e7597a900197a4947`，7065 字符）
* 抽出的正文窗口：`[5153, 7065)`，1912 字符
* 产出：`s01_reviewer_responses.json`、`s01_current_text_window.md`、`s01_analysis.json`

## S02 — CH04-S02

* 现象：verdict 判 closed，quote 与正文只有 LaTeX 空白差异（如 `\int _ {0}` vs `\int_{0}`）
* 上游缓存：`work/model-cache/sha256:46e9529d1ae4db4822c57d97619a57a1ab1c589c29fd3ac2d009e7ea8e41541b.json`, `work/model-cache/sha256:1a3d4d22ba4432590b17183a032cd0cc3c3383164c8fc3608a1103f7524aaeb9.json`
* 上游 usage 行：[40, 42]
* current_text：`data/books/complex-analysis-v2/runs/run-20261006-142529-bad4aa/work/legacy/lesson/lessons/CH04-S02.json`（sha256 `168ebfdcfe4dfa7f73d4bbe95e27cf264ba0abee1ad5bc99d26fc543031767ae`，body_markdown sha256 `010c260cf35b1e55f3ed48a02906479b7ed9b3dac31c8dc0d1c522e9c01c9100`，9808 字符）
* 抽出的正文窗口：`[1682, 6643)`，4961 字符
* 产出：`s02_reviewer_responses.json`、`s02_current_text_window.md`、`s02_analysis.json`

