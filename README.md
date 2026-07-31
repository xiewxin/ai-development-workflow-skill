# AI Development Workflow Skill

[English](README.en.md) | 繁體中文

這是一個同時支援 Codex 與 Claude Code 的公開 Skill，用可驗證的流程協助完成需求計畫、測試設計、Git Diff 審查與端到端實作。

## 技術與相容性

- Skill 格式：Agent Skills（`SKILL.md`）
- 支援工具：Codex、Claude Code
- 文件格式：Markdown、YAML
- 發布驗證：Bash、Python 3 標準函式庫
- 版本管理與審查：Git

## 四種模式

- **需求計畫**：整理目標、邊界、影響、複用、風險與驗收方式；存在且相關時會讀取領域 `CONTEXT` 與 ADR，缺少時不強制建立。AI 協作成效與本機計時預設關閉，只有使用者明確要求或目標倉庫政策要求時才加入並量化。
- **測試設計**：設計正常、邊界、異常與回歸情境，並對應自動化與手動驗證。
- **Git Diff 審查**：分別檢查 Spec／範圍與 Standards／工程品質，驗證並去重後使用目前需求對話內穩定的 `REV-*` 編號、高／中／低嚴重度與狀態追蹤問題。
- **完整流程**：依序進行需求計畫、測試設計、核准後實作、驗證、文件回填與 Git Diff 審查。

## 外部工作流整合

- 四種模式仍是完整原生路徑。只有使用者進入其中一種模式或明確要求跨 Skill 開發交付協調時，才在需求計畫、測試設計、實作、驗證與修復、文件同步及 Git Diff 審查階段評估外部能力。
- 能力有兩個輸入：主動發現只接受平台本輪提供的 Skill catalog metadata；顯式調用上下文只接受使用者已透過平台在目前任務直接調用的能力，不重新發現、排名或調用。發現不等於啟用，兩者都不掃描本機，也不因安裝狀態、品牌或名稱建立能力。
- 待核驗能力為零／一／多項時，快速路徑會直接回退、跳過虛假比較，或只展開目前最高優先組；metadata 初篩不直接建立候選，任何路徑都不省略授權、副作用、所有權、強制合同與可驗證增益。
- 候選先通過可用性、調用模式、授權、副作用、產物所有權與強制合同門檻，再依可驗證增益和一致優先序選用。沒有合格候選時靜默使用原生流程。
- Model-invoked 能力依平台合同觸發；User-invoked 能力只輸出一項目前平台可執行的顯式調用指示並暫停，完成後重新驗證產物再接續。README 不維護第三方靜態命令清單。
- 每個需求最多一個需求級工作流所有者；階段能力執行者只承接獨立能力，外部正式產物保留唯一可寫所有者。本 Skill 只橋接必要的來源、狀態、缺口與同步結果。
- 跨 Provider 能力組合只允許互不重疊的能力槽或明確上下游；同槽與能力包只選一個主執行者，每條跨 Provider 邊都需輕量產物交接合同。
- 計畫已足以直接執行時不預設產生 tickets；只有長期追蹤、複雜協作或外部 tracker 確有增益時才交接任務排序能力。
- 只有使用者需要行動、額外授權、衝突裁決或跨任務恢復時才顯示或保存緊湊交接；不把內部快照、排名或淘汰過程寫入計畫。
- 單一外部工作流已完整、安全且獲授權時，本 Skill 退出多餘橋接；外部能力失效時按實際副作用安全降級，不宣稱 Provider 已通過。
- 整合不會自動安裝、setup、初始化、提交、封存、刪除、遠端寫入或發布。

## 需求計畫特性

- 先自行查證環境事實，再對會改變範圍、合同或方案的決策逐題確認並附建議答案。
- 按需讀取現有領域上下文、決策地圖與 ADR，對照目前程式碼驗證；不為補格式建立額外文件。
- 只在適用時整理使用者或外部系統可觀察的行為與驗收場景，不為湊格式產生冗長 User Stories。
- 小型、單倉庫且沒有外部產物或高擴散風險的需求使用緊湊檔位；需求計畫以六個核心標題、測試設計以五個核心標題交付，複雜需求才展開完整欄位目錄。
- 使用 `AC-* → S-* → T-* → D-*／RUN-*` 串接驗收、切片、情境、資料與執行；具體命令及逐情境結果只由測試設計擁有，避免跨文件漂移。
- 優先選擇使用者可觀察的最高且穩定公開介面作為測試 seam；既有低層測試不能充分驗證可見合同時，可在該公開介面新增測試並取得核准。
- 實作以可獨立驗證的垂直切片、阻塞關係與完成判準排序；Wide refactor 採 `expand → migrate → contract` 並設整合關卡。

## 參考計時與提效

- AI 協作成效與參考計時預設關閉；只有使用者明確要求 AI 成效／提效，或目標倉庫政策要求時才啟用。
- 啟用後以 Python 3 標準函式庫的短命令記錄 session 閉合區間；不啟動常駐程序，也不為估算額外重讀整個倉庫。
- 成效只量化時間；不收集、不估算、不輸出 Token 用量。
- 狀態只保存在使用者本機的專用狀態目錄，不寫入目標倉庫、不上傳，也不記錄需求內容、程式碼、檔名或倉庫名。
- 計時只在目前對話以已持有的隨機 ID 繼續；續接回合以單一 `resume --new-turn` 恢復。等待使用者、CI 或外部佇列前先暫停，不把等待時間算入工作耗時。
- 人工參考基準由已核准計畫的五階段 PERT 在實作前鎖定。計時可涵蓋完整需求，或在實作前才啟用時從下一個未開始階段量化剩餘交付範圍；範圍外階段使用 `0/0/0`，局部結果不得稱為整案提效。
- 只有宣告範圍內完整覆蓋、基準有效且指紋一致時，腳本才輸出節省工時與比例。報告將公式結果表述為「參考工時節省比例」；部分或未知覆蓋只回報實測耗時與異常。
- 同一對話完成後新增 V2／V3 範圍時，使用新的獨立計量分段，不恢復舊狀態或手工合併不同分段。
- 新對話不自動搜尋、繼續或合併舊計量，同一需求換對話後不計算整體參考提效。
- 如使用者已安裝並主動選擇 ActivityWatch，可以本機 AFK 活躍區間與 session 求交集；只使用 loopback GET，不讀取 window bucket，失敗時降級為 session。
- Python 3 不可用、使用者停用或本機安全檢查失敗時，不自動安裝依賴，直接繼續原工作流程並標示無法計算參考提效。
- 此功能不建立跨需求索引、雲端分析或背景清理服務。

## 安裝

### 推薦：使用 skills CLI

環境需具備 Node.js 與 `npx`。執行以下命令後，可互動選擇安裝到哪些 AI 工具、目前專案或全域環境，以及使用 symlink 或 copy：

```bash
npx skills add https://github.com/xiewxin/ai-development-workflow-skill.git \
  --skill ai-development-workflow
```

若要直接全域安裝到 Codex 與 Claude Code，可使用非互動命令：

```bash
npx skills add https://github.com/xiewxin/ai-development-workflow-skill.git \
  --skill ai-development-workflow \
  -g -a codex -a claude-code -y
```

安裝後重新開啟對話，讓工具載入新的 Skill。

### 交給 AI 安裝

可以將以下內容直接交給支援命令執行的 AI 工具：

```text
請參考 https://github.com/xiewxin/ai-development-workflow-skill#安裝，
幫我安裝 Skill：ai-development-workflow。
若我尚未指定，請先依序確認要安裝到哪些 AI 工具，以及安裝到目前專案或全域環境。
```

代理應先檢查 `npx` 是否可用；確認 AI 工具與安裝範圍後，再以包含 `-a`、必要時的 `-g`，以及 `-y` 的 `npx skills add` 命令完成安裝，不應未經確認直接採用預設值。

### 替代方式

#### Codex 官方安裝器

可使用 Codex 內建的官方 `skill-installer` 從 `xiewxin/ai-development-workflow-skill` 安裝 `skills/ai-development-workflow`：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo xiewxin/ai-development-workflow-skill \
  --path skills/ai-development-workflow
```

#### 手動複製

在已取得本倉庫內容的根目錄執行。

Codex：

```bash
mkdir -p ~/.codex/skills
cp -R skills/ai-development-workflow ~/.codex/skills/ai-development-workflow
```

Claude Code：

```bash
mkdir -p ~/.claude/skills
cp -R skills/ai-development-workflow ~/.claude/skills/ai-development-workflow
```

`SKILL.md` 遵循 Agent Skills 格式，Codex 與 Claude Code 共用同一份內容，無需維護兩份 Skill。

## 使用範例

- 「請先整理這個功能的需求計畫，暫時不實作。」
- 「依核准的計畫建立測試設計，包含資料策略與回歸範圍。」
- 「請以目標分支為基準審查完整 Git Diff。」
- 「請用完整流程處理目前需求；如果平台本輪提供能帶來可驗證增益的協同 Skill，請在需要我操作或授權時給我一項明確交接。」
- 「需求已完成，請回填可驗證的 AI 協作貢獻，並依已鎖定 PERT 與本機計量摘要計算參考提效。」
- 「請完成這個需求；在計畫核准、需要我操作、額外授權或衝突裁決時停下。」

## 更新

使用 skills CLI 安裝時，可執行：

```bash
npx skills update ai-development-workflow
```

以上命令用於專案級安裝；更新全域安裝時加上 `-g`：

```bash
npx skills update ai-development-workflow -g
```

手動安裝時，取得最新版本並檢視差異，再以新的 `skills/ai-development-workflow` 取代本機同名目錄。更新後重新開啟對話，讓工具載入新版本。

## 發布前驗證

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
bash tests/test-validate-publication.sh
bash scripts/validate-publication.sh
```

validator 在倉庫模式掃描公開工作目錄（排除 `.git`、`.idea` 及明確定義為 Git 忽略過程產物的 `docs/plans/`、`docs/specs/`），檢查 Skill 結構、元資料、參考計時腳本、Markdown 相對連結、基本範本章節、可選 AI 成效範本的完整欄位、繁體中文及疑似敏感資訊。其他相似目錄不會被排除；錯誤只列出相對路徑、規則與必要行號，不回顯命中內容。

Skill 執行時的互動語言跟隨使用者，文件與程式碼跟隨目標倉庫規範；本倉庫 publication validator 的繁體中文檢查只保護本倉庫公開文件，不會把繁體中文強制套用到其他目標倉庫。

## 語言 allowlist

若公開的固定外部合同必須保留原始詞彙，可在本機根目錄建立 `.publication-language-allowlist`，每行格式為：

```text
<相對檔案路徑>|<完整固定合同詞>
```

空行與以 `#` 開頭的說明會被忽略。allowlist 只放行指定檔案的指定語言詞；憑證、個資、內部網路與本機路徑等安全規則仍會阻擋。此檔案只留在本機，不應發布。

## 安全與隱私

- 公開範例僅使用虛構、中立資料；請勿提交真實業務資料、個資、憑證、內部網址或本機路徑。
- 發布檢查僅為輔助，不能取代人工差異審查與 GitHub Secret Scanning。

## License

本專案採用 [MIT License](LICENSE)。
