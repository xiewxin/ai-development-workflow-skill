# AI Development Workflow Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一個可公開安裝、同時支援 Codex 與 Claude Code 的 AI 研發工作流 Skill。

**Architecture:** 使用單一 `SKILL.md` 作為模式選擇與流程入口，將需求計畫、測試設計、Git Diff 審查及範例拆入按需載入的 references，並以 assets 提供文件範本。專案根目錄提供安裝說明與發布前安全檢查，不在 Skill 中保存個人統計或真實專案資料。

**Tech Stack:** Markdown、YAML、Shell、Agent Skills 開放格式、Git

---

### Task 1: 建立基準情境

**Files:**
- Create: `tests/scenarios.md`

- [x] **Step 1: 定義失敗基準**

建立至少三個完全虛構的情境，分別檢查需求計畫完整性、測試與文件閉環、Git Diff 審查品質及敏感資訊處理。每個情境先定義可觀察的通過條件，不以特定文案作為答案。

- [x] **Step 2: 在未提供 Skill 的情況執行情境**

將原始情境交給獨立代理，不提供預期答案或既有討論結論。

- [x] **Step 3: 記錄實際缺口**

在 `tests/scenarios.md` 記錄可重現的缺口、不一致與代理理由，作為 Skill 最小內容依據。若全部基準原本已通過，先加入合理變體或重新評估 Skill 必要性，不刻意扭曲情境製造失敗。

### Task 2: 初始化可攜式 Skill

**Files:**
- Create: `skills/ai-development-workflow/SKILL.md`
- Create: `skills/ai-development-workflow/agents/openai.yaml`
- Create: `skills/ai-development-workflow/references/`
- Create: `skills/ai-development-workflow/assets/`

- [x] **Step 1: 使用官方初始化工具**

Run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/init_skill.py" ai-development-workflow --path skills --resources references,assets --interface 'display_name=AI Development Workflow' --interface 'short_description=建立需求計畫、測試設計與程式碼差異審查的完整工作流' --interface 'default_prompt=使用 $ai-development-workflow 處理目前需求並在每個確認點停下。'
```

Expected: 建立 Skill 骨架與 `agents/openai.yaml`。

- [x] **Step 2: 驗證 RED 狀態**

Run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/ai-development-workflow
```

Expected: 骨架仍包含 TODO 或內容不足，尚未通過完整專案驗證。

實際結果：骨架包含初始化 TODO，符合 RED 狀態；本機 `quick_validate.py` 因缺少 `PyYAML` 無法執行，依規格保留給發布檢查 fallback 驗證，不修改全域 Python。

### Task 3: 實作核心工作流與 references

**Files:**
- Modify: `skills/ai-development-workflow/SKILL.md`
- Create: `skills/ai-development-workflow/references/requirement-plan.md`
- Create: `skills/ai-development-workflow/references/test-design.md`
- Create: `skills/ai-development-workflow/references/git-diff-review.md`
- Create: `skills/ai-development-workflow/references/examples.md`

- [x] **Step 1: 實作模式選擇與共用規則**

在 `SKILL.md` 保留四種模式、證據優先級、寫入確認、繁體中文、安全與 reference 載入規則，frontmatter 只使用 `name` 與 `description`。

模式路由必須區分：明確單一／多模式請求只執行指定範圍；端到端實作請求進入完整流程；已有核准計畫時從未完成階段續行；「審查並修復」保留在審查模式並將原請求視為範圍內修復授權；涉及合同變更、擴大需求、破壞性操作或計畫偏離時仍停下確認；無法判斷時只問一個範圍問題。

- [x] **Step 2: 實作需求計畫規則**

寫入來源讀取、專案探索、文件真實性驗證、跨專案缺口、複用分析、分層、落盤、迭代及 AI 協作成效規則。

- [x] **Step 3: 實作測試設計規則**

寫入情境格式、自動化與手動驗證、測試資料、SQL 安全、`/tests` 映射及實作後回填規則。

- [x] **Step 4: 實作 Git Diff 審查規則**

寫入 base 判斷、已提交與本機變更範圍、審查維度、優先級、短格式、無問題輸出及唯讀預設。

- [x] **Step 5: 加入精簡虛構範例**

範例只使用中立名稱及占位資料，展示輸入、計畫片段、測試情境、問題與無問題審查格式。

- [x] **Step 6: 實作完整流程協調規則**

明確定義需求計畫、測試設計、計畫核准、目前代理實作、文件回填與 Git Diff 審查的順序；文件寫入遵循模式矩陣，程式碼實作必須等計畫明確核准。發現新事實或方案偏離時，先列出證據與影響，取得確認並更新計畫後再繼續。

### Task 4: 實作文件範本

**Files:**
- Create: `skills/ai-development-workflow/assets/requirement-plan-template.md`
- Create: `skills/ai-development-workflow/assets/test-design-template.md`

- [x] **Step 1: 建立需求計畫範本**

包含所有必填章節、狀態清單、文件改動及 AI 協作成效，避免說明文字過長。

- [x] **Step 2: 建立測試設計範本**

包含情境、測試類型、資料策略、手動 SQL 注意事項、實作結果及剩餘風險。

- [x] **Step 3: 連結範本與使用時機**

在 `requirement-plan.md` 與 `test-design.md` 明確連結相應 asset，說明新建文件時以範本為骨架、既有文件依專案慣例更新；避免範本成為無法發現的孤立檔案。

### Task 5: 建立公開安裝文件與安全檢查

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `scripts/validate-publication.sh`
- Create: `tests/test-validate-publication.sh`

- [x] **Step 1: 先建立發布檢查失敗測試**

使用暫存目錄及虛構資料，驗證檢查程式會阻擋私鑰、常見憑證格式、個資占位資料、內部 URL、本機家目錄路徑、簡體中文禁用詞、失效相對連結、缺少的必要目錄、無效或缺少必要欄位的 `SKILL.md` frontmatter、範本必填章節及未取代占位符；另驗證有效 frontmatter 與正常內容可以通過，錯誤輸出不回顯疑似 secret 值。負向 fixture 以字串分段組合，且區分範本允許的輸入標記與真正未完成的開發占位符，避免全量掃描命中測試本身。

- [x] **Step 2: 執行測試並確認失敗**

Run:

```bash
bash tests/test-validate-publication.sh
```

Expected: FAIL，因 `validate-publication.sh` 尚未實作。

實際結果：測試先在 validator 尚未完成時失敗，並重現敏感資訊、結構、連結、元資料與符號連結邊界缺口；實作與回歸案例補齊後轉為 GREEN。

- [x] **Step 3: 實作最小發布檢查**

使用 `find` 或 `rg --files --hidden -g '!.git/**'` 掃描目前工作樹的所有預期發布檔案，而非只掃描已追蹤檔案。檢查必要結構、只含 `name` 與 `description` 且值有效的 `SKILL.md` frontmatter、Skill 與 reference 到 asset 的可達連結、範本必填章節、繁體中文禁用詞、私鑰、常見憑證、敏感 URL、Email／電話樣式、本機家目錄路徑、未完成占位符及可選本機 blocklist；輸出檔案與命中規則但不回顯疑似 secret 值。allowlist 只允許記錄外部固定合同的語言誤報，不得略過敏感資訊規則。

- [x] **Step 4: 執行測試並確認通過**

Run:

```bash
bash tests/test-validate-publication.sh
```

Expected: PASS。

實際結果：`bash tests/test-validate-publication.sh` 輸出「發布檢查測試全數通過」。

- [x] **Step 5: 撰寫 README**

提供 Codex 與 Claude Code 的安裝方式、四種使用模式、隱私注意事項、更新方式及驗證命令，不包含內部專案資訊。

### Task 6: 驗證 Skill 行為與發布內容

**Files:**
- Modify: `tests/scenarios.md`
- Modify: `skills/ai-development-workflow/**`（僅在驗證發現問題時）

- [x] **Step 1: 執行 Skill 結構驗證**

Run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/ai-development-workflow
```

Expected: 外部驗證器可用時輸出 `Skill is valid!`。若 `skill-creator` 或其 Python 依賴不可用，記錄原因並使用下一步的 `validate-publication.sh` 驗證必要結構與 frontmatter；不得省略 fallback，也不得把外部工具缺失誤判為 Skill 內容通過。

實際結果：官方 `quick_validate.py` 因本機缺少 `PyYAML` 而無法啟動，錯誤為 `ModuleNotFoundError: No module named 'yaml'`；未修改全域 Python，改用下一步的專案 validator 完成必要 fallback。

- [x] **Step 2: 執行 reference 與格式檢查**

Run:

```bash
bash scripts/validate-publication.sh
```

Expected: PASS，且必要結構、相對連結、範本章節、繁體中文及安全檢查均通過。

實際結果：`bash scripts/validate-publication.sh` 輸出「發布檢查 PASS」。

- [x] **Step 3: 使用 Skill 重跑代理情境**

將 Skill 與原始虛構情境交給獨立代理，依既定檢核表確認需求計畫、測試設計、審查、簡潔度與安全規則沒有退化，且基準已發現的缺口均已改善。若仍有關鍵條件失敗，修訂 Skill 後重測；若基準沒有缺口，記錄合理變體與 Skill 是否仍提供一致性價值。

- [x] **Step 4: 回填驗證結果**

實際結果：需求計畫與 Git Diff 審查情境通過；測試設計首次 GREEN 因篇幅與重複內容未通過，修正規模裁剪、資訊唯一來源與生命週期後重測通過。Claude Code 尚未實機載入的相容性風險已記錄於 `tests/scenarios.md`。

在 `tests/scenarios.md` 記錄通過項、偏差及未實機驗證 Claude Code 的剩餘風險。

- [x] **Step 5: 最終本機檢查**

Run:

```bash
git diff --check
git status --short
```

Expected: 已追蹤差異沒有空白錯誤；只有本專案預期檔案。未追蹤檔案在 Task 7 暫存後再使用 `git diff --cached --check` 完整驗證。

實際結果：Shell 語法、發布測試、正式 validator 與 `git diff --check` 均通過；`git status --short` 只有本專案預期的未追蹤檔案。

### Task 7: 建立本機提交並停止於推送確認點

**Files:**
- Modify: `docs/superpowers/plans/2026-07-21-ai-development-workflow-skill.md`

- [x] **Step 1: 更新計畫完成狀態與驗證結果**

實際結果：三組 GREEN 情境完成；測試設計在第一次 GREEN 發現篇幅問題後修正並重測通過；最終整體規格審查與品質審查均為 APPROVED。Claude Code 尚未實機載入的剩餘風險已保留。

- [x] **Step 2: 再次執行敏感資訊與差異檢查**

實際結果：提交前重新執行 Shell 語法、validator 完整測試、正式發布檢查及 staged whitespace 檢查；實際命令與結果以本次提交證據為準。

- [x] **Step 3: 建立本機 Git 提交**

先確認發布檢查已掃描所有未追蹤及已追蹤檔案，且差異中沒有本機絕對路徑、內部資訊或敏感資料，再執行：

```bash
git add .
git diff --cached --check
git commit -m "feat: add portable AI development workflow skill"
```

Expected: staged 差異檢查無輸出後才建立提交；若檢查失敗，停止提交、修正並重跑發布檢查。

實際結果：staged 差異檢查先發現 fixture Diff 的空白問題，修正且確認 fixture 仍可套用後重新驗證；最終以 `feat: add portable AI development workflow skill` 建立本機 root commit。

- [x] **Step 4: 停止並等待確認**

不要建立 GitHub 遠端、公開倉庫或推送分支；向使用者交付本機路徑、驗證結果及剩餘風險。

實際結果：GitHub 公開倉庫與 `origin` 由使用者建立及設定；本次未推送，完成本機提交後等待使用者選擇首次發布方式。
