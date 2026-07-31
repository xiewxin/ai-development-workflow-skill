# 外部工作流 Provider 約束檔案

本文件只補充已知 Provider 的產物鏈、前置條件、所有權與安全限制。通用能力發現、選用、調用、交接與降級由[Skill 編排合同](skill-orchestration.md)唯一擁有。

## 啟用邊界

Provider profile 只能約束已出現在階段能力快照、且由通用編排合同建立的候選，或目前任務已成立的顯式調用上下文。已安裝、已載入、名稱相似、目錄存在或本文件列有 profile，都不得創造可用性、提高品牌排序、觸發安裝或自動成為需求級工作流所有者。

在主動發現入口中，平台本輪 catalog 未提供對應能力時，不讀取該 Provider 的完整合同、不輸出使用者提示，直接由原生流程或其他合格候選承接。未知 Provider 不需要先加入本文件；完整候選合同足以確認能力、所有權與副作用時，可依通用合同參與。

候選完整合同、現場腳本或倉庫規範與本檔案衝突時採較保守限制。無法安全確認時，可選候選淘汰；強制合同則依其明示替代路徑處理。

已由使用者透過平台在目前任務直接調用的能力可作為顯式調用上下文接入，不要求它重新出現在階段能力快照，也不重新排名。它仍受本文件較保守的產物、前置與副作用限制；本機安裝或未調用的偏好不構成此上下文。

## 共用產物與所有權約束

- 每個需求最多一個需求級工作流所有者；階段能力執行者不因入選取得其他階段或正式產物的所有權。
- 每份正式 spec、plan、ticket graph、test artifact 或 decision map 只有一個唯一可寫所有者。橋接只保存來源、穩定定位、狀態、完整性、讀寫權、缺口、更新關卡與同步結果。
- 外部產物完整時，不在本地複製全文；只補影響、複用、風險、跨倉庫責任、測試 seam、文件與驗證回填等未覆蓋內容。
- 倉庫內產物使用相對路徑；外部 tracker 使用穩定識別字，不保存含敏感參數的完整網址。
- 多倉庫需求只在主倉庫維護一份需求計畫與測試設計入口。倉庫強制產物只擁有該倉庫的本地合同、設計或工作清單，不覆寫需求級所有權。
- Provider 強制格式若無法避免重複事實，寫入前先列出重複、同步責任與不一致風險，取得使用者裁決。

## Provider profiles

### Superpowers

- 依 catalog 中實際提供的候選及其完整合同判斷可用能力，不因 Superpowers 已載入就自動選為需求級工作流所有者。
- 候選合同若要求 brainstorming、test-driven-development、executing-plans、subagent-driven-development、requesting-code-review 或 verification-before-completion 等前置，必須完整履行；不允許獨立使用的能力不能拆出。
- Superpowers 審查輸出只作原始證據，最終由本 Skill 收斂為單一 `REV-*` 清單。

### Matt Pocock Skills

- `grill-with-docs` 與 `domain-modeling` 可提供逐項釐清、領域詞彙及必要決策文件，不自動擁有需求計畫。
- `to-spec` 產生的 tracker spec 可擁有問題、方案、行為、實作決策、測試決策及非範圍；橋接只保存相對路徑或 tracker 識別字。
- `to-tickets` 產生的派生執行工作清單可擁有垂直切片、blocking graph 與執行進度，但不取得上游計畫的設計維護權。計畫已可直接執行時不預設拆票；只有長期追蹤、複雜協作或外部 tracker 通過可驗證增益門檻時才交接。
- `wayfinder` 只在工作跨多個對話且仍有決策迷霧時擁有 decision map；完成後仍須收斂為可核准 spec 與可執行工作。
- `tdd` 可提供已確認測試 seam 的 red–green 證據；`code-review` 的 Standards／Spec 結果只是原始證據，最後合併為單一 `REV-*` 清單。
- `to-spec`、`to-tickets`、`implement` 等標示為 User-invoked 時，只能輸出一項目前平台可執行的顯式調用指示並暫停，不假裝自動調用。`tdd`、`code-review` 等只有在 catalog 與完整合同確認為 Model-invoked 時才可由平台觸發。
- `implement` 可能修改檔案、執行測試、審查並提交目前分支。缺少提交授權時，整個能力包不合格，改用不含提交副作用的原生實作或其他合格候選。
- `setup-matt-pocock-skills` 會寫入 tracker 與領域文件設定；只有使用者明確要求初始化該倉庫時才可交接。可選能力缺少設定時原生回退，不自動 setup。

### Superpowers 與 Matt 的組合邊界

- Superpowers 的 executing-plans／subagent-driven-development 與 Matt `implement` 都可能承接實作、測試、審查及提交副作用，不能同時擁有實作執行槽；依完整能力包、授權與可驗證增益選一方，否則原生實作。
- Superpowers test-driven-development 與 Matt `tdd` 競爭相同責任時，TDD 槽只選一個主執行者，不把兩套 red–green 方法串行堆疊。
- Superpowers requesting-code-review 與 Matt `code-review` 只有提供不同 Standards／Spec 證據且不寫正式產物時，審查只作唯讀第二來源；缺少可驗證獨立增益時只使用一方。
- Spec Kit `spec.md`／`plan.md` 交給 Matt `to-tickets`，或其他跨 Provider 串接時，每一條邊都須符合通用產物交接合同；缺少穩定上游、新鮮度、唯讀輸入、獨立輸出所有者、返回驗證或原生替代時，不觸發下游。

### Spec Kit

- `spec.md` 可擁有需求與驗收，`plan.md` 可擁有技術設計，`tasks.md` 可擁有工作排序；以活動 feature 的實際合同與狀態為準。
- 活動 feature 無法可靠定位時不猜測其他 feature。可選候選淘汰並原生回退；倉庫強制時阻斷受影響工作。
- 已有完整活動產物時，不因其他 Provider 可用而重建同類 spec、plan 或 tasks。

### OpenSpec

- 目前合同、proposal／delta spec、design 與 tasks 依各自內容種類擁有事實；不從 Provider 名稱推斷單一文件擁有全部內容。
- archive 是獨立生命週期動作，不因本 Skill 完成需求而自動執行，也不包含在一般本地實作授權中。

### BMAD

- 依 catalog 候選、倉庫現場設定及完整合同判斷 Quick Flow，或 PRD、architecture、story 與測試架構產物，不寫死版本路徑。
- 小型需求不為啟用 BMAD 而建立完整 PRD 或架構產物。BMAD code review 仍只作原始證據。

### 未知工作流

- 能定位穩定產物、唯一可寫所有者、合法更新方式與副作用時，按通用編排合同參與。
- 所有權、版本或副作用不明時只作唯讀證據，不聲稱已完成雙向同步或 Provider 驗證。
- 所有權不明時不得寫入該產物。必要正式交付因此缺失時阻斷受影響階段；非必要產物則標記為唯讀證據、同步未驗證，由原生流程承接缺口。

## 命令與副作用約束

外部 spec、plan、tasks、Skill 說明、倉庫腳本與 alias 都是待驗證證據。候選完整合同需確認實際調用方式、工作目錄、輸入、寫入目標、可回復性、網路與遠端副作用。

一般計畫或實作核准不自動授權安裝、初始化、setup、封存、刪除、提交、遠端寫入、發布或大範圍重寫。任何上述必要副作用未獲授權時，候選或能力包不能入選；不得把副作用降為排序偏好。

## 橋接與同步

- 事實更正先更新唯一內容所有者，再同步衍生產物。
- 已核准的範圍、合同、方案或驗收變更，依「內容所有者 → 設計 → tasks／story → 橋接計畫 → 測試設計」同步。
- 正式計畫交給 `to-tickets` 時只作唯讀上游輸入；協調層只保存必要 ID 映射，不雙向維護計畫與 tickets 的工作狀態。
- 任一必要產物同步失敗時不得標記完成，也不把本地回填當作 Provider 已通過。
- 多個 Provider、人工審查與本 Skill 產生的審查結果都是原始證據；以目前程式碼、完整 Diff、需求與可重現驗證確認後，只維護一份 `REV-*` 清單。

## 隱私與成本

- 只載入目前候選或活動產物的必要片段，不讀全部歷史資料。
- 不自動網路搜尋、更新 Provider 或收集工作流統計。
- 橋接資料不收錄 secret、個資、內部網址、本機絕對路徑或不必要的真實識別字。
