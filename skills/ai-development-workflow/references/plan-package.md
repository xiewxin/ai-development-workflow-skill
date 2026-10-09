# 計畫包合同

本文件定義需求級計畫包的身份、產物職責、核准、執行交接與相容讀取。新生成內容只使用目錄式計畫包；舊平鋪文件只作受限相容讀取，不自動移動或刪除。

## 固定路徑與生命週期

每個需求使用一個穩定目錄：

```text
docs/plans/YYYY-MM-DD-<topic>/
├── design.md
├── delivery.md
├── implementation.md
├── test-design.md
├── manifest.json
├── execution.json
└── tasks/                 # 條件式；預設不生成
```

`topic` 使用簡短 kebab-case。同日同主題已存在時建立 `-v2`、`-v3` 新目錄，不覆蓋歷史包。`docs/plans/` 是 Git 忽略的過程產物，不得提交；公開 Skill、PR 與 release 不攜帶實際需求計畫包。

生命週期分為：

1. **草擬**：建立四份 Markdown 正式產物及兩份 JSON；`manifest.json` 尚未含核准雜湊，`execution.json` 為未開始。
2. **已核准、待最終化**：一次確認四份文件的 SHA-256 與 `execution_mode`、`worktree_policy`、`commit_policy`；按已核准條件機械派生 Task 後最終化 manifest。
3. **執行中**：執行者先驗證外部核准紀錄、最終 manifest 與檔案雜湊，再以 `implementation.md` 為唯一執行入口，只把實際狀態寫入 `execution.json`。
4. **已完成或已取代**：完成後保留證據；已核准內容變更需在新目錄退回草擬並重新核准，不覆寫既有核准身份。取代關係記在新包的來源引用與舊包的 execution 偏差紀錄。

## 產物的單一職責

每項事實只有一個唯一事實來源；其他文件使用精確相對路徑與穩定 ID 引用，不複製全文。

`test-design.md` 是 `RUN-*` 驗證命令的唯一來源；為保持單一入口可直接執行，implementation 以 RUN ID 標記機械摘錄的完整命令與 Expected，核准前逐字對帳，不能獨立改寫。非測試的實作／Git 操作由 implementation 擁有。需要改驗證命令時先改 test-design 的新版本草稿，再同步摘錄，一起重新核准。

| 產物 | 唯一擁有內容 | 不擁有內容 |
| --- | --- | --- |
| `design.md` | 做什麼、為什麼、架構與資料流、介面、替代方案、設計風險、非目標 | 任務步驟、執行命令、實際結果 |
| `delivery.md` | 目標、範圍、現況證據、`AC-*`、交付風險、文件處置、最終驗收 | 架構論證、逐步實作、詳細測試案例 |
| `implementation.md` | 可直接執行的任務、完整程式碼、精確路徑與命令、Expected、Interfaces、依賴、`AC-*／S-*／T-*` 映射 | 重述需求背景、設計替代方案、實際執行結果 |
| `test-design.md` | 測試矩陣、邊界、資料、關鍵斷言、`T-*／D-*／RUN-*`、驗證命令 | 實作步驟、架構決策、實際執行狀態 |
| `manifest.json` | 計畫包身份、核准狀態、四份正式文件 SHA-256、執行與授權策略 | 命令輸出、動態任務進度 |
| `execution.json` | 實際任務狀態、命令、測試結果、commit SHA、偏差與完成時間 | 修改核准計畫或反向成為需求來源 |

需要改變範圍、合同、方案、驗收或實作步驟時，在新版本草稿更新擁有該事實的文件及其引用，再重新計算全部正式文件 SHA-256 並核准。只修正 `execution.json` 的觀測結果不需要重批計畫。核准後不得勾選正式文件內的 checkbox、修改設計狀態或把 Provider ledger 回填到正式 Markdown；checkbox 表示預定步驟，完成狀態只記在 execution。

## implementation.md 執行合同

`implementation.md` 是所有執行型工作流的統一入口，格式可供 `superpowers:executing-plans` 與 `superpowers:subagent-driven-development` 直接讀取，不需要格式轉換；是否可啟用仍須通過下方相容性矩陣。其他 Provider 只透過中立執行合同讀取它；本 Skill 不因此成為程式碼執行器。

每個 Task 是可被新執行者獨立理解、驗證與審查的最小交付單位：

- 每個操作約 2–5 分鐘，使用 checkbox 追蹤。
- 列出精確檔案路徑；修改既有檔案時附 symbol 或可驗證定位。
- 程式碼步驟提供完整可用內容，不使用 `TBD`、`TODO`、省略號或「同前」。
- 每個命令附精確工作目錄、命令及 Expected；Expected 必須能判定成功或正確的 RED 失敗。
- 每個 Task 列出 Interfaces、Dependencies、allowed files，以及 `AC-*／S-*／T-*` 映射。
- 每個 Task 首次寫入前記錄 HEAD 及 staged／unstaged／untracked 清單；Task Diff review 分別檢查這三種狀態，實際讀取新增檔案，並對照 Task 起始基線歸屬變更，不能把空的 unstaged diff 當作審查通過。
- 依 TDD 排列 RED → 驗證正確失敗 → GREEN → 驗證通過 → refactor；每個 Task 結束前審查該 Task Diff。
- 最後執行完整累計驗證、完整 Diff 範圍對帳與最終審查。
- 若核准的 `commit_policy` 允許本地逐 Task commit，commit 步驟可包含在各 Task；否則不得臨時新增 commit。

## 計畫身份與核准

`manifest.json` 的 `plan_package_id` 識別一個核准版本。首次建立時產生並保持不變；重新核准時使用新目錄與新的 plan_package_id，保留舊包原始位元組。核准與最終化順序：

1. 確認四份正式 Markdown 已無未決策占位符，且相互引用可解析。
2. 以檔案原始位元組計算 SHA-256；不得在雜湊前改換換行、編碼或格式化。
3. 在使用者可見、位於包外的外部核准紀錄中綁定包 ID、四份檔案雜湊、三項策略、`source_revision`（核准時完整 Git commit SHA）與唯一 `execution_id`；`approval_record` 在核准時固定指向核准、收據與領用狀態的唯一紀錄位置，預設為目前對話，`approved_at` 記錄核准時間。若原需求核准來自唯讀 tracker，在目前對話引用其核准來源，不把後續狀態拆到另一個未被 manifest 指定的位置。只有 manifest 自稱 approved 不能證明核准。核准基線須可取得；未提交變更不能冒充 source revision 的一部分，與計畫輸入重疊時先解決身份差異再核准。
4. 先核准四份正式文件與執行策略，再機械派生符合已核准條件的 Task 並填入 `derived_tasks`。不增加步驟、權限或範圍的精確摘錄不需要第二次內容核准；需要新決策時停止並重新核准。沒有 Task 時保留空陣列。
5. 把 push、PR、merge、release、publish、deploy、remote_write、api_mutation 固定標記為 `separate_authorization`；本地 commit 只有在 `commit_policy` 明示時才屬整包授權。
6. 驗證派生項後填寫 `finalized_at`；對完成的 `manifest.json` 計算 SHA-256，供 `execution.json.manifest_sha256` 綁定，並把包 ID 與最終 digest 回報至 approval_record 指定的紀錄作為交接收據。預設回報目前對話；tracker 寫入另需授權。若選用 tracker 作為紀錄位置，每一次 tracker／API 狀態寫入（包含 active、claimed、completed、superseded、revoked）都必須在動作前取得針對該次寫入的明確獨立授權；最初核准不能打包涵蓋後續寫入，execution、worktree、commit 三項策略也不授權此副作用。沒有該次授權時停止該寫入，不能自行改換狀態來源規避。收據是核准內容的機械最終化，不是新增內容核准；manifest 不自我引用，execution 也不是核准錨點。

只有 `finalized_at` 不是 `null` 且外部收據可核對才可執行。任何正式文件雜湊不符、狀態不是 `approved`、執行策略缺失、核准紀錄不可取得或外部動作被錯誤標為已授權時，都不得開始執行。核准後不可原地重算 manifest 或重新填寫 finalized_at 來合理化差異。

每個 execution_id 使用一次性執行收據；最終 digest 收據的初始狀態為 `active`。首次開始前，協調者須讀取同一核准紀錄的最新外部狀態，並追加 `claimed` 收據，綁定 execution_id、manifest digest、source_revision 與目標 worktree 身份；追加後回讀確認，才可執行。`active` 僅能被同一協調者領用一次，重複／併發領用或狀態無法判定時停止；沒有原子領用能力的對話只允許單一協調者，不得跨會話併發執行同一包。

恢復執行必須是同一 execution_id、同一 worktree 與同一動態 execution 紀錄，且最新狀態仍為 `claimed`；不得以新建 execution.json 重置進度。完成後追加 `completed`，取代時在舊包外部紀錄追加 `superseded` 並引用新包 ID，撤銷時追加 `revoked`；三者皆不得重用。舊 manifest 保持原始 approved 位元組，效力由最新外部狀態決定。重新 materialize 到另一 worktree、重跑已完成包或無法核對外部狀態時，需要新包與新核准，不得憑舊 digest 啟動。以上收據預設寫在目前對話；遠端狀態寫入同樣受明確授權限制。

## Worktree materialization

批准計畫可 materialize 到隔離 worktree，但不是一般目錄的無條件複製：

1. 先建立或確認同一倉庫的目標隔離 worktree，再做 materialization，最後才啟動執行型 Skill；Git 忽略的包不會隨 worktree checkout 出現。複製前核對外部核准紀錄及收據，在來源倉庫重新計算四份正式文件 SHA-256，並逐項驗證派生 Task 的內容 SHA、父 implementation SHA 與 schema。
2. 僅允許複製 manifest 列出的四份正式文件與 `manifest.json`；`execution.json` 在目標 worktree 依範本建立新的未開始狀態。條件式 Task 只有列入 manifest 的 `derived_tasks` 才可複製。
3. 目標必須是同一倉庫的隔離 worktree，且使用相同相對路徑 `docs/plans/YYYY-MM-DD-<topic>/`。用 Git common directory 身份確認同倉庫；首次實作前目標 HEAD 必須等於 source_revision，且新隔離 worktree 的 tracked／untracked 工作內容須為乾淨基線（忽略的計畫包除外）。不得把錯誤或過時分支的 HEAD 記成 execution base 來放行。驗證來源與目標所有路徑元件，拒絕符號連結、非一般檔案、路徑穿越與逃離包根目錄的解析結果。目標已存在時停止，不覆蓋或合併；既有包恢復執行走身份重驗而非重新 materialize。
4. 複製後再次重新計算 SHA-256，逐項驗證四份文件、每個派生 Task 與 manifest，並把已核對外部收據的目標 manifest SHA 寫入新的 `execution.json`。
5. 執行前第三次驗證核准狀態、全部 allowlist 檔案 SHA、執行模式、worktree 與 commit 策略。複製驗證到執行之間若檔案再變動，停止交接並重驗，不沿用舊結果。

不得複製秘密、憑證、個資、未核准文件、allowlist 以外的檔案或既有動態 `execution.json`。來源或目標驗證失敗時停止，不以重新產生 manifest 掩蓋差異。

## 條件式 tasks/

預設不生成 `tasks/`。只有符合至少一項可驗證條件時，才從已核准的 `implementation.md` 派生 Task 執行包：並行執行、跨會話交接、跨倉庫協調，或高風險隔離。

每個 Task 文件必須綁定父計畫相對路徑、父 `implementation.md` SHA-256、Task ID、`AC-*`、依賴與 allowed files。它只摘錄執行該 Task 所需的精確步驟與引用，是派生執行包，不是第二份事實來源；設計、範圍或驗收變更必須回到父計畫重新核准。Task 檔名使用 `tasks/<task-id>.md`，並列入 `manifest.json.derived_tasks`。

派生包也須攜帶下述 Provider bridge 要求的完整必要上下文，以及父 Task 的 Evidence handoff；使用 [Task 範本](../assets/task-template.md) 的對應槽位機械摘錄並記錄來源定位。動態依賴結果不抄成核准事實，只引用同一 execution 的實際紀錄。所有有依賴的 Task（包含未派生者）啟動前，須核對各前置 Task 已 completed、測試與 Task Diff review 通過、所需介面／產物可用，且具備 commit_policy 要求的真實 commit；在 execution 保存核對證據。缺失、pending 或不符時停止，不能因程式碼已存在就放行。

`derived_tasks` 的每個項目固定包含 `task_id`、`path`、Task 檔案 `sha256` 與 `parent_implementation_sha256`；空陣列表示沒有批准任何派生 Task。執行者不得只靠目錄掃描發現或加入 Task。

`derived_tasks` 必須是陣列。Task ID 使用 `S-` 加至少兩位數；ID 與 path 都不得重複；path 只能是與該 ID 完全相符的 `tasks/S-01.md` 形式，禁止絕對路徑、反斜線、空元件與 `..`。兩個 digest 都必須是 64 位小寫十六進位，父 digest 必須等於 manifest 中的 implementation SHA。來源與目標的 tasks 目錄及檔案均不得為符號連結；解析後必須仍位於該包內。派生內容須逐項對回父 Task 的步驟、AC、依賴與 allowed files；雜湊相等只能證明位元組相同，不能代替此內容對帳。

## execution.json 回填

執行者在每個命令完成後立即記錄實際命令、工作目錄、時間、exit code 與結果摘要；測試另記 `T-*`／`RUN-*`、實際結果與證據。每個 Task 記錄狀態、實際變更檔案、Task Diff review 結果及 commit SHA；未 commit 時填 `null`，不可虛構。

開始實作前確認 Git HEAD 等於已核准的 source_revision，再記錄為 `base_commit_sha`，並把既有 staged、unstaged、untracked 檔案清單記入首次命令證據；current-checkout 也遵守相同 revision 與重疊變更檢查。恢復同一次執行時允許已記錄的本地 Task commits，須核對基線祖先關係、完整 commit／Diff 鏈與外部 claimed 收據，不能套用首次執行的空白狀態。完整 Diff review 必須涵蓋此基線之後的已提交與未提交變更，另行檢查未追蹤的新檔案；不能只審查最後一次 commit 或目前未提交 Diff。

發生偏差時先記錄原步驟、新事實、影響與是否需要重新核准。超出 allowed files、改變 AC、接口、方案、實作步驟或授權策略時停止並重新核准；純執行事實可記錄後繼續。命令失敗或需改命令時記錄失敗證據，再依核准計畫既有替代步驟處理；沒有已核准替代步驟時停止，不能只以「不改合同」自行放行。最終累計驗證、完整 Diff review 與剩餘風險也只寫入 `execution.json`，不回寫成核准計畫事實。

每個 commands 項目固定包含 `run_id`、`planned_run_id`、`workdir`、`actual`、`recorded_at`、`exit_code`、`result`；每個 tests 項目包含 `test_id`、`run_id`、`actual`、`recorded_at`、`evidence`、`status`。`run_id` 是單次命令觀測的唯一 ID，在全部 Task commands 與 cumulative_verification 中不得重複；RED、GREEN、重試或再次累計驗證分配不同 run_id，`planned_run_id` 指回測試設計的原始 RUN ID（非測試操作為 null）。test.run_id 必須引用同一 execution 內存在的 command run_id，不能懸空或用 planned_run_id 代替觀測。尚未執行的觀測值為 `null`，不得保留生成占位符。`cumulative_verification` 使用相同 commands 結構；`final_commit_sha` 記錄 final-local-commit 的 SHA，逐 Task SHA 留在該 Task。commit 成功後才讀取 Git SHA 並回填。`deviations` 每項記錄 `task_id`、`original_step`、`new_fact`、`impact`、`requires_reapproval` 與 `resolution`。JSON 只接受固定 schema 欄位；唯一可選欄位 `ai_collaboration` 為字串陣列，保存已明確啟用的計量摘要與證據索引。狀態值與型別依 JSON 範本及發布檢查的 schema 約束。

交接時明示當前 execution.json 的唯一寫入者與回收寫入責任的時點，不讓協調者與實作代理同時改寫同一檔案。委派回填時，brief 必須提供適用的完整欄位合同及可定位的 execution 範本，涵蓋 commands、tests 與 deviations 的欄位名、型別、ID／相對路徑格式及跨欄位關聯；只有空陣列或「回填結果」指示不足以構成輸出合同。驗證須對照既有 schema，不以只核對欄位名的自訂檢查冒充完整驗證。未委派寫入時，實作代理交回原始觀測及證據位置，由協調者依 schema 回填。`recorded_at` 表示實際記錄時刻；未即時採集的執行時間不得推算補造，須保留原始紀錄並明示缺口。修正 JSON 結構不代表補回缺失的歷史證據。

`completed` 必須同時具備開始／完成時間、已核對基線、所有 Task 的完成狀態、已執行命令、通過測試與證據、Task Diff review、成功的累計驗證及最終 Diff review；空陣列、null 時間或 not_run 不得支援完成宣稱。commit_policy 為 final-local-commit 時，完成狀態還必須有非 null 且格式正確的 final_commit_sha；none／task-local-commits 不得填 final_commit_sha。task-local-commits 下，每個 completed Task 必須有非 null 且格式正確的 commit_sha。RED 的預期失敗可保留為歷史命令，但完成 Task 的最後驗證須成功。publication schema 可檢查這些欄位關聯，無法證明填寫的觀測值真實。

commands、tests 與 cumulative_verification 依實際觀測順序追加，保留 RED、失敗與獲准重試，不排序或刪除歷史來通過完成門禁。Task 完成時，每個 test_id 的最後觀測須 passed；累積驗證按 `(planned_run_id, workdir)` 分組，無 planned_run_id 時按 `(actual, workdir)` 分組，每組最後觀測須 exit 0。不同驗證項或不同目錄的成功不能抵銷未解決的失敗；RUN ID 只標識觀測，不代表排序。此判定不授權重試或改命令，仍須遵守既有偏差／重新核准規則。

發布檢查只驗證公開範本的結構與欄位語義，不讀取 Git 忽略的真實需求包，也不證明外部核准、實際檔案雜湊或 worktree materialization 成功。執行者仍須完成上述實體驗證；本 Skill 不增加必要執行環境。

## 舊格式受限相容

讀取階段暫時接受既有 `docs/plans/YYYY-MM-DD-<topic>.md` 與 `docs/plans/YYYY-MM-DD-<topic>-test-design.md`，但先標記為 `legacy_flat`：

- 可作歷史意圖與證據索引，不因存在就視為已核准或可執行。
- 執行前仍需補成新計畫包並取得核准；不在讀取時自動轉換。
- 不自動移動、改名、覆蓋或刪除歷史計畫。
- 新生成、改版或重新核准的內容只寫入目錄式計畫包。

## 安全與 Provider bridge

計畫批准不擴張外部副作用。push、PR、merge、release、publish、部署、API mutation 與其他遠端寫入永遠保持獨立授權；安裝、setup、刪除與封存仍依 Provider 合同另行判定。API mutation 包含發送訊息與寫入外部資料，不因它被稱作測試就視為已授權。Provider 可讀 `implementation.md` 與 manifest 的中立欄位，但不能改寫正式產物所有權、繞過雜湊驗證或把 `execution.json` 當成第二份計畫。

### Superpowers 相容性矩陣

以下為可啟用條件，不是對所有版本的相容保證；選用時讀取本輪實際 Skill 的完整合同，將結果與版本或檔案 digest 記在 execution 的偏差／證據。能力不能滿足核准策略時不合格，改用已核准的相容執行者；切換 execution_mode 需重新核准。

| 合同面向 | executing-plans | subagent-driven-development |
| --- | --- | --- |
| 入口與 header | 直接讀 implementation.md，依核准模式啟用 | 同一入口；只在實際可用且已核准時使用子代理；不得只交付 Task 摘錄，brief 必須攜帶下述完整全域內容 |
| 工作區 | 要求 isolated-worktree 的版本不能配 current-checkout | 同左；先建工作區、完成 materialization，再建立 ledger |
| commit | 執行內容與收尾能力均須遵守 commit_policy | 預設逐 Task commit 的版本只接受 task-local-commits；none 或 final-local-commit 若不能遵守則不合格 |
| ledger／todos | 僅作操作索引，實際結果同步 execution | ledger 可保留 Provider 恢復索引；必須綁定完整 plan 路徑、包 ID 與 manifest SHA，不能只靠 implementation basename；同 workspace 衝突時停止 |
| 正式產物 | 不修改核准的 checkbox、狀態或步驟 | 同左；Provider brief 只是暫存摘錄，不自動成為 manifest 批准的 tasks |
| 偏差裁決 | 超出核准合同必須停止並重新核准 | 要求自行 ruling 的版本也必須接受 Global Constraints；無法遵守時不合格 |
| 收尾 | finishing 能力不能自動擴張 push、merge、publish 或刪除權限 | 清理 ledger 前須把完整 rulings、證據與恢復資訊寫入 execution 並核對；清理仍需既有授權 |

生成 implementation header 時只保留已核准的執行模式。`inline` 或 `provider` 不可保留 REQUIRED Superpowers 指令；Superpowers 模式僅指定已核准且通過矩陣的 Skill，不能讓執行者自行改選另一模式。同一執行槽只有一個所有者。

implementation 的 Global Constraints 必須自含會影響執行的精確值（介面/schema、限制、允許路徑、source revision、執行與 commit 策略），引用只用於溯源，不能取代值。這些是正式來源的機械摘錄，核准前逐字對帳。SDD 控制者建立每個 brief 時，須把完整 Global Constraints、execution policy、Spec 及必要依賴介面與 Task 原文一併交付，並在派送前核對；只會抽取 `### Task` 區塊且無法攜帶上下文的版本不合格，不能宣稱可直接兼容。

Provider 的 brief 提取結果須按 Markdown 標題層級核對邊界，不能只以「直到下一個 Task」判定結尾。最後一個 Task 後的 `Final cumulative verification` 等同級或更高層級章節仍由協調者擁有，不隨 Task 派發給實作代理。保留原始提取結果供查證；允許把目標 Task 與上述必要上下文機械組合為暫存 brief，並記錄來源位置及內容對帳。這不改寫正式計畫或新增 Task；無法可靠區分內容所有權時停止交接。
