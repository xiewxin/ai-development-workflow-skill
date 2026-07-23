## AI 協作紀錄與成效

本章節預設關閉；只有使用者明確要求 AI 成效／提效，或目標倉庫政策明確要求時，才附加到需求計畫。參考計時的啟用、基準、狀態與清理依[參考計時指南](../references/reference-timing.md)執行。效率只量化時間；不收集、不估算、不輸出 Token 用量。

### 可驗證貢獻

- 需求規模：{{INPUT:小型｜中型｜大型及可檢查的範圍依據}}
- 協作範圍：{{INPUT:實際使用的需求計畫、測試設計、實作輔助、驗證及 Git Diff 審查}}
- 產出與驗證：{{INPUT:實際修改、測試、文件及可重現驗證結果摘要}}
- 提前發現與避免返工：{{INPUT:提早識別的具體問題、影響與處置，沒有則填無}}
- 人工決策與介入：{{INPUT:由使用者確認的合同、取捨、資料、驗收或發布決策}}

### 效率量化

- 計量 ID：{{INPUT:start 回傳的隨機 ID}}
- 計量模式與資料來源：{{INPUT:啟用範圍，以及 complete 實際使用的 session｜ActivityWatch}}
- 計量覆蓋度：{{INPUT:complete｜partial｜unknown、判定證據；非 complete 時不得計算節省工時或提效}}
- 階段級 PERT：{{INPUT:五個固定階段的 O/M/P 整數秒、範圍、複用、測試、文件與風險依據；未鎖定時說明原因}}
- 人工參考基準與鎖定時間：{{INPUT:PERT 總秒數、換算工時、實作前鎖定時間；無效時填未鎖定}}
- 基準指紋：{{INPUT:baseline 與 complete 對帳的指紋；未鎖定時填無}}
- AI 協作參考耗時：{{INPUT:complete 回傳總秒數與換算工時；無可靠區間時填無法計算}}
- 階段摘要：{{INPUT:requirement_plan、test_design、implementation、verification_fix、docs_review 聚合秒數}}
- 參考節省工時：{{INPUT:人工參考基準減 AI 協作參考耗時；基準無效時填無法計算及原因}}
- 參考提效比例：{{INPUT:參考節省工時除以人工參考基準；負值如實保留，無效時不填 0%}}
- 可信度：{{INPUT:中｜低，以及判定依據}}
- 異常與混入工作：{{INPUT:anomalies、mixed_work=no｜yes｜unknown 與影響；沒有則填無}}
- 歸因限制：{{INPUT:參考值邊界，以及人員熟練度、需求清晰度、既有複用、離線工作與工作環境等影響}}
- 狀態清理結果：{{INPUT:需求計畫回讀對帳結果，以及 delete 成功｜保留及原因}}
