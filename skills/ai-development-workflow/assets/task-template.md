# {{INPUT:Task ID}} — {{INPUT:Task 名稱}}

> 本文件是 [父計畫]({{INPUT:../implementation.md}}) 的派生執行包，不是第二份事實來源。任何設計、範圍、驗收或步驟變更都必須回到父計畫重新核准。

- 父計畫路徑：`docs/plans/{{INPUT:YYYY-MM-DD-topic}}/implementation.md`
- 父計畫 SHA-256：`{{INPUT:64-lowercase-hex}}`
- Task ID：`{{INPUT:S-01}}`
- 驗收：`{{INPUT:AC-*}}`
- 測試：`{{INPUT:T-*}}`
- 依賴：{{INPUT:無或前置 Task ID 與原因}}
- Allowed files：`{{INPUT:精確相對路徑清單}}`

## 必需上下文

{{INPUT:從父 implementation.md 逐字摘錄完整 Global Constraints、Execution policy、Spec 及本 Task 的 consumes／produces 介面，附各段來源定位；引用不能取代精確值。只作機械投影，不新增或改寫父事實。}}

## 啟動前核對

- 執行身份：`{{INPUT:execution_id}}`；實際紀錄：`{{INPUT:execution.json 的可定位路徑}}`。
- 依賴門禁：{{INPUT:無依賴則寫 None；否則列出各前置 Task ID 與證據定位。啟動前核對同一 execution 中前置 Task 已 completed、測試與 Task Diff review 通過、產物介面可用，且具備 commit_policy 要求的真實 commit。證據缺失、pending 或不符時停止，不以程式碼已存在代替。}}
- 依 manifest 核對本派生檔案 SHA、父 implementation SHA 及內容投影；不符時停止，不重算 manifest 放行。

## 執行步驟

{{INPUT:逐字摘錄父 implementation.md 中此 Task 的完整 checkbox、程式碼、命令與 Expected，不得改寫}}

## 返回合同

- 唯一寫入者與責任交還時點：{{INPUT:逐字摘錄父 Task 的 Evidence handoff。未委派寫入時，worker 只交回原始觀測及證據位置，由 controller 回填 execution.json；委派寫入時，附適用的 commands/tests/deviations 完整欄位合同及可定位 execution 範本，涵蓋型別、ID／相對路徑格式與跨欄位關聯。}}
- 實際結果只記入 `execution.json` 中相同 Task ID；不回寫核准計畫。`recorded_at` 使用實際記錄時刻，不推算缺失的歷史時間。
- 父計畫雜湊、allowed files 或依賴不符時停止，不自行擴張。
