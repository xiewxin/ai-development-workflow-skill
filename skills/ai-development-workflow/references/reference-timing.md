# AI 協作參考計時指南

## 適用時機

- 完整流程預設啟用，首次只簡短說明「計量狀態僅存本機，可隨時停用」，不以確認問題阻斷探索。
- 需求計畫、測試設計或 Git Diff 審查等單一模式，只在使用者明確要求計時時啟用。
- 使用者拒絕、Python 3 不可用、狀態目錄不安全或執行環境不適合時，關閉計時並繼續主流程；完結時標示無法計算參考提效。
- 計時用於單一需求的參考與趨勢比較，不代表精確人工工時或 AI 的單一因果貢獻。

## 執行入口與九個命令

在 Skill 根目錄以 Python 3 執行 `scripts/measure.py`。Windows 可改用 `py -3`。以下 ID 是虛構範例：

```bash
python3 scripts/measure.py start --phase requirement_plan --provider session
python3 scripts/measure.py baseline --id 0123456789abcdef0123456789abcdef \
  --estimate requirement_plan=1200,1800,2400 \
  --estimate test_design=1200,1800,2400 \
  --estimate implementation=7200,9000,10800 \
  --estimate verification_fix=3000,3600,4200 \
  --estimate docs_review=1200,1800,2400
python3 scripts/measure.py enter --id 0123456789abcdef0123456789abcdef --phase test_design
python3 scripts/measure.py pause --id 0123456789abcdef0123456789abcdef
python3 scripts/measure.py resume --id 0123456789abcdef0123456789abcdef
python3 scripts/measure.py recover --id 0123456789abcdef0123456789abcdef --exclude-open
python3 scripts/measure.py complete --id 0123456789abcdef0123456789abcdef --mixed-work no
python3 scripts/measure.py status --id 0123456789abcdef0123456789abcdef
python3 scripts/measure.py delete --id 0123456789abcdef0123456789abcdef
```

- `start`：建立隨機計量 ID，鎖定 Provider 與初始階段。
- `baseline`：在產品實作開始前，以五階段 PERT 鎖定人工參考基準與指紋。
- `enter`：切換階段；running 時會同時閉合前一區間。
- `pause`：閉合目前區間，每個 AI 回合結束前執行。
- `resume`：在同一對話的後續回合開啟新區間。
- `recover --exclude-open`：排除無法還原的未閉合區間，記錄異常並降低可信度。
- `complete`：只在 paused 時封存，依 `no|yes|unknown` 記錄是否混入其他工作。
- `status`：以已持有的 ID 唯讀取得精簡狀態，不提供列舉或反查。
- `delete`：需求計畫回填且回讀確認後刪除 completed 狀態。活動狀態只能在使用者明確要求且使用雙重確認時刪除。

## 固定階段

| 階段 | 範圍 |
| --- | --- |
| `requirement_plan` | 需求理解、證據探索與計畫 |
| `test_design` | 測試策略、資料與情境設計 |
| `implementation` | 產品程式碼與自動化測試實作 |
| `verification_fix` | 驗證、問題修正與重跑 |
| `docs_review` | 文件回填與完整 Git Diff 審查 |

不適用的 PERT 階段明確傳入 `0,0,0`，不新增自訂階段，避免基準與計時範圍不一致。

## 狀態轉換

| 目前狀態 | 命令 | 結果 |
| --- | --- | --- |
| 無 | `start` | 建立 running 並開啟初始區間 |
| running | `enter` | 閉合舊區間並開啟新階段；同階段為無作用 |
| running | `pause` | 閉合區間並轉為 paused |
| paused | `enter` | 只更新階段，不新增耗時 |
| paused | `resume` | 轉為 running 並開啟區間 |
| running | `recover --exclude-open` | 排除未閉合區間，轉為 paused 並降可信度 |
| paused | `complete` | 封存 completed 聚合摘要 |
| completed | `complete` | 刪除前回傳同一封存摘要 |
| completed | `delete` | 回填對帳後清除狀態 |

## PERT 基準與指紋

- 需求範圍、檔案級工作、測試、文件與風險穩定後，再依已驗證計畫為每階段產生樂觀 `O`、一般 `M`、保守 `P` 的整數秒。
- 每階段必須滿足 `0 <= O <= M <= P`，且附範圍、複用、測試、文件與推高保守值的風險依據。
- 階段參考秒數為 `round((O + 4 * M + P) / 6)`；五階段總和必須大於零。
- `baseline` 只能在產品實作階段尚未開始時首次鎖定。相同數值重送為無作用；鎖定後不得依實際結果修改。
- 指紋由正規化 PERT 與鎖定時間產生。完結時指紋不一致，只保留參考耗時，不計算節省工時或比例。

## 每回合的低成本流程

1. 首次進入完整流程執行 `start --phase requirement_plan`，把回傳 ID 寫入之後建立的需求計畫。
2. 階段切換執行 `enter`；每個 AI 回合交回使用者前執行 `pause`。
3. 同一對話的後續回合，先以已持有 ID 執行 `status`。paused 才 `resume`；若意外保留 running，不把等待時間納入，改用 `recover --exclude-open`。
4. 計畫核准且實作前，先把 PERT 依據與數值寫入需求計畫，再執行 `baseline`。
5. 完結前先 `pause`，判斷是否混入其他工作；證據不足只問一個簡短問題，仍無法判斷時傳入 `unknown`。
6. 執行 `complete`，把聚合摘要回填需求計畫；回讀對帳 ID、指紋、耗時、異常與混入工作結論後，才執行 `delete`。

## 混入工作、異常與跨對話

- `mixed-work=yes` 或 `unknown` 一律降為低可信度，不以手工扣除秒數掩蓋問題。
- 未閉合區間不直接計到當下；只能排除並記錄 `open_interval_excluded`。
- 時間倒退、區間重疊、狀態損壞、指紋不一致或寫入失敗都不繼續猜測。
- 新對話不搜尋、列舉、解析、繼續或合併舊計量。同一需求若必須換對話，本版不另建續接計量，最終標示無法計算整體參考提效。

## 本機狀態與隱私

- 狀態只包含隨機 ID、Provider、階段、UTC epoch、閉合區間、PERT 數值與指紋、異常碼、可信度及 completed 聚合摘要。
- 不保存需求、提示、程式碼、檔名、倉庫名、本機路徑、視窗標題、應用程式名或 ActivityWatch 原始事件。
- 狀態位於使用者本機狀態目錄，不寫入 Git 工作樹、不提交、不上傳；各 ID 以獨立排他鎖與原子取代保護，鎖檔建立與清理再由不含 ID 的短時存續鎖協調。
- 不建立背景清理、雲端分析或跨需求索引。

## ActivityWatch 可選升級

- 只有使用者選擇 `--provider activitywatch` 才讀取本機 API；預設 Provider 仍是 session。
- 預設使用 `localhost` 的 `5600` port；如需其他 loopback port，以 `AI_WORKFLOW_ACTIVITYWATCH_URL` 設定。主機名稱只接受 `localhost` 或 loopback IP literal，不接受其他可解析到 loopback 的網域；URL 只允許無 userinfo 的 HTTP，所有請求固定為 GET 且逾時兩秒。
- 只選取本機上 `type=afkstatus`、`client=aw-watcher-afk` 的唯一 bucket，且只統計 `status=not-afk` 事件與 session 閉合區間的交集。不查詢 window bucket。
- 無候選、多候選、回應無效、逾時、非 loopback 或導向外部主機時，記錄 `activitywatch_fallback`、降為低可信度並使用 session。
- 不自動安裝、啟動或設定 ActivityWatch。

## 回填與清理

`complete` 後將下列聚合欄位寫入需求計畫：計量 ID、模式與資料來源、階段級 PERT、人工參考基準與鎖定時間、基準指紋、AI 協作參考耗時、階段摘要、參考節省工時、參考提效比例、可信度、異常與混入工作、歸因限制與狀態清理結果。

- 缺少有效 baseline 時仍回填參考耗時，但節省工時與比例填「無法計算：未在實作前鎖定人工參考基準」。
- 結果為負值時如實保留，不改寫為提升；`unknown` 不得美化為無混入工作。
- 先回讀需求計畫確認聚合值、ID 與指紋，再 `delete`。清理後不保留該 ID 的狀態或專用鎖檔，只以計畫中的聚合資料追溯，不宣稱可還原事件級明細。
