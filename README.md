# AI Development Workflow Skill

這是一個同時支援 Codex 與 Claude Code 的公開 Skill，用可驗證的流程協助完成需求計畫、測試設計、Git Diff 審查與端到端實作。

## 技術與相容性

- Skill 格式：Agent Skills（`SKILL.md`）
- 支援工具：Codex、Claude Code
- 文件格式：Markdown、YAML
- 發布驗證：Bash、Python 3 標準函式庫
- 版本管理與審查：Git

## 四種模式

- **需求計畫**：整理目標、邊界、影響、複用、風險與驗收方式；完成後回填可驗證的 AI 協作貢獻，具備實作前鎖定基準與本機計量摘要時才計算參考提效。
- **測試設計**：設計正常、邊界、異常與回歸情境，並對應自動化與手動驗證。
- **Git Diff 審查**：依完整差異與程式碼證據對帳核准範圍，使用目前需求對話內穩定的 `REV-*` 編號、高／中／低嚴重度與狀態追蹤問題。
- **完整流程**：依序進行需求計畫、測試設計、核准後實作、驗證、文件回填與 Git Diff 審查。

## 參考計時與提效

- 完整流程預設以 Python 3 標準函式庫的短命令記錄 session 閉合區間；不啟動常駐程序，也不為估算額外重讀整個倉庫。
- 狀態只保存在使用者本機的專用狀態目錄，不寫入目標倉庫、不上傳，也不記錄需求內容、程式碼、檔名或倉庫名。
- 計時只在目前對話以已持有的隨機 ID 繼續。新對話不自動搜尋、繼續或合併舊計量，同一需求換對話後不計算整體參考提效。
- 人工參考基準由已核准計畫的五階段 PERT 在實作前鎖定；完結時由腳本輸出參考耗時、節省工時、提效比例、可信度與異常。數值用於參考與趨勢，不宣稱精確工時或 AI 的單一因果貢獻。
- 如使用者已安裝並主動選擇 ActivityWatch，可以本機 AFK 活躍區間與 session 求交集；只使用 loopback GET，不讀取 window bucket，失敗時降級為 session。
- Python 3 不可用、使用者停用或本機安全檢查失敗時，不自動安裝依賴，直接繼續原工作流程並標示無法計算參考提效。
- 此功能不建立個人 CSV、跨需求索引、雲端分析或背景清理服務。

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
- 「需求已完成，請回填可驗證的 AI 協作貢獻，並依已鎖定 PERT 與本機計量摘要計算參考提效。」
- 「請完成這個需求，依完整流程在每個確認點停下。」

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
bash tests/test-validate-publication.sh
bash scripts/validate-publication.sh
```

validator 會掃描工作目錄中的檔案（排除 `.git` 與 `.idea`），檢查 Skill 結構、元資料、參考計時腳本、Markdown 相對連結、範本章節與 AI 成效必填欄位、繁體中文及疑似敏感資訊。錯誤只列出相對路徑、規則與必要行號，不回顯命中內容。

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
