# AI Development Workflow Skill

這是一個同時支援 Codex 與 Claude Code 的公開 Skill，用可驗證的流程協助完成需求計畫、測試設計、Git Diff 審查與端到端實作。

## 技術與相容性

- Skill 格式：Agent Skills（`SKILL.md`）
- 支援工具：Codex、Claude Code
- 文件格式：Markdown、YAML
- 發布驗證：Bash、Python 3 標準函式庫
- 版本管理與審查：Git

## 四種模式

- **需求計畫**：整理目標、邊界、證據、方案、風險與驗收方式。
- **測試設計**：設計正常、邊界、異常與回歸情境，並對應自動化與手動驗證。
- **Git Diff 審查**：依實際差異與程式碼證據檢查正確性、合同、回歸、測試與範圍。
- **完整流程**：依序進行需求計畫、測試設計、核准後實作、驗證、文件回填與 Git Diff 審查。

## 安裝

### Codex

可使用 Codex 內建的官方 `skill-installer` 從 `xiewxin/ai-development-workflow-skill` 安裝 `skills/ai-development-workflow`：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo xiewxin/ai-development-workflow-skill \
  --path skills/ai-development-workflow
```

也可手動複製技能目錄：

```bash
mkdir -p ~/.codex/skills
cp -R skills/ai-development-workflow ~/.codex/skills/ai-development-workflow
```

安裝後於新的 Codex 對話中使用。

### Claude Code

將同一個目錄複製到 Claude Code 的 Skill 路徑：

```bash
mkdir -p ~/.claude/skills
cp -R skills/ai-development-workflow ~/.claude/skills/ai-development-workflow
```

`SKILL.md` 遵循 Agent Skills 格式，Codex 與 Claude Code 共用同一份內容，無需維護兩份 Skill。

## 使用範例

- 「請先整理這個功能的需求計畫，暫時不實作。」
- 「依核准的計畫建立測試設計，包含資料策略與回歸範圍。」
- 「請以目標分支為基準審查完整 Git Diff。」
- 「請完成這個需求，依完整流程在每個確認點停下。」

## 更新

取得最新版本後，先檢視差異，再以新的 `skills/ai-development-workflow` 取代本機同名目錄。更新後重新開啟對話，讓工具載入新版本。

## 發布前驗證

```bash
bash tests/test-validate-publication.sh
bash scripts/validate-publication.sh
```

validator 會掃描工作樹中的已追蹤與未追蹤檔案（排除 `.git`），檢查 Skill 結構、元資料、Markdown 相對連結、範本章節、繁體中文與疑似敏感資訊。錯誤只列出相對路徑、規則與必要行號，不回顯命中內容。

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
