# 專案規範

- 修改前先閱讀相關 `docs/agents` 與目前程式碼。
- Controller 只處理輸入與輸出，業務流程放在 Service。
- Repository 只由 Service 呼叫。
- 優先複用現有能力，避免重複驗證與查詢。
- 新增行為必須補充自動化測試及相關文件。
