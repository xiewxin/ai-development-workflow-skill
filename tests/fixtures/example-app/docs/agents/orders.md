# 訂單模組

建立訂單由 `OrderController` 呼叫 `OrderService`。折扣驗證統一使用 `PromotionService::validateCode()`，此方法會檢查有效期限與使用狀態。

本文件可能落後目前程式碼，修改前必須驗證實際呼叫鏈路。
