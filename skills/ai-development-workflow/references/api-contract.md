# 接口契約與驗收

只有新增或變更 HTTP／RPC／事件接口時讀取；純內部修改不建立空契約文件。接口契約是計畫、測試、實作與驗收的共同依據，不是額外接口管理平台。

## 唯一來源與位置

1. 先查明接口與既有權威來源（OpenAPI、JSON Schema、版本化文檔或可定位的接口平台版本）。已有來源時更新該來源，計畫包只保存精確引用與本次變更；不另維護同內容副本。無法讀取或版本不明時列出缺口，不猜測既有包裝、狀態碼或錯誤碼。
2. 沒有權威來源時，在 `docs/plans/YYYY-MM-DD-<topic>/contracts/` 建立適用的 `api.md`、`<operation>.request.schema.json`、`<operation>.response.schema.json`；需要不同失敗結構時另建或引用共用失敗 Schema。使用[接口範本](../assets/api-contract-template.md)，只保留適用內容。
3. 包內文件列入 manifest 的 `contract_files`；無包內契約時使用空物件。已有包外來源以其版本／路徑／operation 定位於 design，不複製到 contract_files。引用不是本次變更的寫入授權；外部平台更新仍需單獨授權。

## 接口內容

- 明確 method、path／operation、鑑權、Content-Type，以及 path／query／header／body 參數各自位置；request body Schema 不代替其他參數約束。不包含憑證真值。
- 請求、正常響應、業務拒絕與接口失敗分開說明，沿用實際 HTTP／業務包裝。列出狀態碼、錯誤標識、可重試性，以及資料與外部通知副作用；不要由超時推論外部操作一定未完成。
- 字段名稱保持實際合同；每個自有 Schema 的根、物件和字段使用中文 `title` 與 `description`。既有外部來源的語言遵循其規範，不為中文標籤複製整套 Schema。
- 明確 `type`、物件 `required`、可空、枚舉及適用的範圍／格式。必填與可空不同；不默認收緊 `additionalProperties`、封閉未知錯誤碼或重命名既有字段。
- 每個字段提供符合實際 JSON 型別的 `examples`，根層提供必要的完整場景。示例與 Mock 都不能代替驗證；`default` 也不代表服務端會自動補值。默認值處理需有實作與測試。
- 使用 Apifox 時提供字段 `x-apifox-mock`，需要排序時提供 `x-apifox-orders`。這些是工具擴展，不是標準約束；Mock 規則是字串，輸出仍須符合 Schema 型別。特別核對數字、boolean、空字串、null 與條件場景，未實測 Apifox 生成時不宣稱 Mock 已驗證。不要為其他工具強加 Apifox 字段。
- Schema dialect／OpenAPI 版本沿用實際 consumer 能力並明示。跨字段條件屬驗收要求時，用 consumer 支援的 Schema 條件或測試斷言表達，不只留在 description。

例如某個可空原因字段的型別示例（示意採用支援聯合 type 的 JSON Schema；不是通用 OpenAPI 版本宣告）：

```json
{
  "type": ["string", "null"],
  "title": "通知原因標識",
  "description": "通知成功時為 null；失敗時為原因標識。保留未知值處理。",
  "examples": [null, "NOTIFICATION_FAILED"],
  "x-apifox-mock": "null"
}
```

## 交給實作與測試

`design.md` 定位唯一來源及必要語義；`implementation.md` 的 Task Interfaces 與 brief 攜帶 operation、Schema 定位及影響執行的精確限制。原文完整可讀的引用與必要摘錄足夠，不把整套契約複製到每個 Task。分派子代理時帶上同一契約及必要依賴，不能只給 Task 標題。若 materialize 到 worktree，先複製並核驗 contract_files，再檢查包外引用在目標中可讀且版本一致；缺少輸入時不能讓實作者自行補決策。

`test-design.md` 將 `AC-* → operation／Schema → T-* → RUN-*` 關聯起來，使用項目既有驗證工具；沒有可用工具時指定人工驗證與限制，不增加全域必裝 runtime。對真實接口的受控測試需驗證兩層：

| 層次 | 必要證據 |
| --- | --- |
| 結構 | 實際參數的接受／拒絕、狀態碼、響應符合 Schema、examples 有效；只解析 JSON 不等於 Schema 驗證 |
| 行為 | 適用的權限、業務拒絕、狀態轉換、冪等與副作用，例如通知失敗不回滾已完成的關聯 |

Mock 只可替代被隔離的外部依賴；回傳固定 Mock 響應通過 Schema，不能證明真實接口已實作。執行結果與偏差寫入 execution，不回填為核准事實。發現實作與契約不符時，判斷為實作缺陷或待確認的契約變更；不能直接改 Schema 迎合錯誤實作。契約變更按計畫包版本與核准流程同步設計、實作、測試及引用。

沒有接口變更時，design 只記一行不適用及依據。本能力不自動啟動 Mock 服務、調用真實 API、寫入接口平台、生成 SDK 或引入新協議框架。
