---
type: meta
tags: [meta]
---
# 叮噹長壽知識庫 — 使用說明

這是一個 **Markdown 知識庫**：本質就是一個裝純文字 `.md` 檔的資料夾，**不綁定任何軟體**。

- **真相來源** = 這些 `.md` 檔
- **閱讀** = 用 `_tools/產生HTML.py` 重生的 HTML 瀏覽器
- **編寫** = 任何文字編輯器，或交給 Claude Code
- **不綁定任何特定 app**：可用任何文字／Markdown 編輯器開啟。
  但這只是其中一種閱讀器，**本庫不依賴它**——`[[連結]]` 與 frontmatter 是我們自己的慣例，HTML 產生器會讀它們。

## 資料夾
- `00 索引地圖` 入口 MOC
- `01 9S框架` 中央樞紐：九支柱 + 三大斷崖 + 核心哲學
- `02 老年醫學證據庫` 地基：每篇文獻一個 note，附查核狀態
- `03 臨床主題` 各臨床議題，連回支柱與證據
- `_tools` 產生器（重生 HTML 的引擎）
- `_範本` 新增 note 範本

## Frontmatter 欄位
證據：type/citation/year/journal/study_type/evidence_grade/verified/verified_date/supports
支柱：type/pillar_code/philosophy

## 查核工作流（鐵則：引用前一律查核）
- `verified: true` 已調全文／確認出處，可用於書籍與正式簡報
- `verified: false` + `#待查核` 用前必須回核
- 搜尋 `#待查核` 可列出所有待辦

## 重生 HTML
```bash
python3 _tools/產生HTML.py
```
**永遠改 `.md`，不要手改 HTML。** HTML 是拋棄式衍生視圖。
（frontmatter 一併保留，供日後若想做即時查詢用——選配。）
