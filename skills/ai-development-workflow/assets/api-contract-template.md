# {{INPUT:接口主題}}契約

> 條件式產物：僅在沒有既有權威契約、且本次新增或變更接口時建立。已有來源只在 design.md 記錄精確引用與變更；不複製本範本。不適用的段落刪除。

## 接口與來源

- 接口：{{INPUT:method＋path 或 RPC／事件 operation}}
- 來源／版本：{{INPUT:需求、已驗證實作與契約版本；新設計不得冒充既有行為}}
- 關聯：{{INPUT:design.md 章節；AC-*；implementation Task；test-design.md 的 T-*}}
- 鑑權與內容格式：{{INPUT:實際鑑權要求、Content-Type，不含憑證}}
- Schema 版本：{{INPUT:項目與 consumer 支援的 dialect／OpenAPI 版本}}

## 請求

| 位置 | 參數／中文名 | 必填／可空／默認處理 | 結構契約 |
| --- | --- | --- | --- |
| {{INPUT:path/query/header/body}} | {{INPUT:實際標識與中文名}} | {{INPUT:實際規則}} | {{INPUT:Schema 相對路徑與 property／pointer，無則說明}} |

## 響應與失敗

| 場景 | HTTP／業務狀態 | 響應 Schema | 完整示例 | 語義與重試限制 |
| --- | --- | --- | --- | --- |
| {{INPUT:成功／業務拒絕／接口失敗}} | {{INPUT:實際狀態}} | {{INPUT:相對路徑及必要引用}} | {{INPUT:Schema 的 examples 定位}} | {{INPUT:業務結果、錯誤及未知值處理}} |

## 行為與副作用

- {{INPUT:狀態轉換、適用的冪等、回滾與外部操作界限；例如主操作成功不代表通知成功}}
- 結構／行為驗收：{{INPUT:引用 test-design.md 的 T-* 與 RUN-*，不重複命令}}

## Schema 與 Mock 交付

- {{INPUT:請求／響應字段具備 type、中文 title／description、適用約束及型別正確的 examples；每個物件明確 required}}
- {{INPUT:使用 Apifox 時的 x-apifox-mock／適用 orders；完整多場景示例與 Mock 驗證方式；未驗證則記限制}}
- {{INPUT:引用解析、Schema 驗證與示例驗證方式，沿用項目工具；不把 Mock 通過當作真實接口通過}}

實際驗收結果只寫 execution.json。契約需變更時回到計畫包重新核准，不以修改本文來掩蓋實作偏差。
