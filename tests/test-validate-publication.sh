#!/usr/bin/env bash

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATOR="${REPO_ROOT}/scripts/validate-publication.sh"
BASH_BIN="$(command -v bash)"

if [[ ! -f "${VALIDATOR}" ]]; then
    echo "失敗：找不到發布檢查程式 scripts/validate-publication.sh"
    exit 1
fi

test_source="$(<"${BASH_SOURCE[0]}")"
required_mktemp_guard='if ! TEST_ROOT="$(mktemp'' -d)"; then'
required_test_root_guard='if [[ -z "${TEST_ROOT}" || ! -d "${TEST_''ROOT}" ]]; then'
if [[ "${test_source}" != *"${required_mktemp_guard}"* || "${test_source}" != *"${required_test_root_guard}"* ]]; then
    echo "失敗：測試暫存目錄缺少安全防護"
    exit 1
fi

if ! TEST_ROOT="$(mktemp -d)"; then
    echo "失敗：無法建立測試暫存目錄"
    exit 1
fi
if [[ -z "${TEST_ROOT}" || ! -d "${TEST_ROOT}" ]]; then
    echo "失敗：測試暫存目錄無效"
    exit 1
fi
if ! TEST_ROOT="$(cd "${TEST_ROOT}" && pwd -P)"; then
    echo "失敗：無法取得測試暫存目錄實體路徑"
    exit 1
fi
trap 'rm -rf "${TEST_ROOT}"' EXIT

failures=0

# 建立一份可通過發布檢查的最小虛構倉庫。
create_valid_repo() {
    local root="$1"
    local skill_root="${root}/skills/ai-development-workflow"

    mkdir -p \
        "${skill_root}/agents" \
        "${skill_root}/references" \
        "${skill_root}/assets"

    printf '%s\n' \
        '---' \
        'name: ai-development-workflow' \
        'description: Use when a public workflow needs a safe validation example.' \
        '---' \
        '' \
        '# AI 開發工作流程' \
        '' \
        '請參考[需求計畫](references/requirement-plan.md#指南)。' \
        '' \
        '字面格式範例：`[優先級][類型] 標題`。' \
        '' \
        '### [P1][功能正確性] 虛構審查範例' \
        > "${skill_root}/SKILL.md"

    printf '%s\n' \
        'interface:' \
        '  display_name: "AI Development Workflow"' \
        '  short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
        '  default_prompt: "使用 $ai-development-workflow 處理目前需求。"' \
        > "${skill_root}/agents/openai.yaml"

    printf '%s\n' '# 指南' > "${skill_root}/references/requirement-plan.md"
    printf '%s\n' '# 測試指南' > "${skill_root}/references/test-design.md"
    printf '%s\n' '# 差異審查' > "${skill_root}/references/git-diff-review.md"
    printf '%s\n' '# 虛構範例' > "${skill_root}/references/examples.md"

    printf '%s\n' \
        '# {{INPUT:需求主題}}' \
        '## 基本資訊／狀態' \
        '## 需求來源與目標' \
        '## 範圍與非範圍' \
        '## 現況與證據' \
        '## 影響分析' \
        '## 複用分析' \
        '## 方案與決策' \
        '## 風險' \
        '## 檔案級實作計畫' \
        '## 實作清單' \
        '## 測試與驗證' \
        '## 文件改動' \
        '## 待確認事項' \
        '## 實作與驗證結果' \
        '## AI 協作成效' \
        '' \
        '[{{INPUT:文件名稱}}]({{INPUT:相對連結}})' \
        > "${skill_root}/assets/requirement-plan-template.md"

    printf '%s\n' \
        '# {{INPUT:測試設計主題}}' \
        '## 基本資訊／關聯' \
        '## 範圍與策略' \
        '## 環境與依賴' \
        '## 測試資料策略' \
        '## 詳細情境' \
        '## 目標自動化映射' \
        '## 手動驗證與可選唯讀 SQL' \
        '## 回歸' \
        '## 交付測試清單' \
        '## 自動化測試實施結果' \
        '## 偏差與剩餘風險' \
        > "${skill_root}/assets/test-design-template.md"
}

# 執行檢查並驗證成功。
expect_pass() {
    local label="$1"
    local root="$2"
    local output
    local status

    output="$("${BASH_BIN}" "${VALIDATOR}" "${root}" 2>&1)"
    status=$?
    if (( status != 0 )); then
        echo "失敗：${label}應通過"
        printf '%s\n' "${output}"
        failures=$((failures + 1))
    fi
}

# 執行檢查並驗證失敗。
expect_fail() {
    local label="$1"
    local root="$2"
    local expected_rule="${3:-}"
    local forbidden_value="${4:-}"
    local output
    local status

    output="$("${BASH_BIN}" "${VALIDATOR}" "${root}" 2>&1)"
    status=$?
    if (( status == 0 )); then
        echo "失敗：${label}應被阻擋"
        failures=$((failures + 1))
        return
    fi
    if [[ -n "${expected_rule}" && "${output}" != *"[${expected_rule}]"* ]]; then
        echo "失敗：${label}未命中預期規則"
        failures=$((failures + 1))
    fi
    if [[ -n "${forbidden_value}" && "${output}" == *"${forbidden_value}"* ]]; then
        echo "失敗：${label}錯誤輸出回顯測試值"
        failures=$((failures + 1))
    fi
}

# 驗證符號連結被拒絕，且錯誤不洩漏根目錄或外部資料。
expect_symlink_fail() {
    local label="$1"
    local root="$2"
    local link_relative="$3"
    local external_path="$4"
    local external_content="$5"
    local output
    local status

    output="$("${BASH_BIN}" "${VALIDATOR}" "${root}" 2>&1)"
    status=$?
    if (( status == 0 )); then
        echo "失敗：${label}應被阻擋"
        failures=$((failures + 1))
        return
    fi
    if [[ "${output}" != *"${link_relative}"* || "${output}" != *"[符號連結]"* ]]; then
        echo "失敗：${label}未使用相對路徑與符號連結規則"
        failures=$((failures + 1))
    fi
    if [[ "${output}" == *"${root}"* || "${output}" == *"${external_path}"* || "${output}" == *"${external_content}"* ]]; then
        echo "失敗：${label}錯誤輸出洩漏外部資料"
        failures=$((failures + 1))
    fi
}

# 驗證循環連結只用 Markdown 來源位置回報，不產生 traceback。
expect_markdown_loop_fail() {
    local label="$1"
    local root="$2"
    local source_location="$3"
    local output
    local status

    output="$("${BASH_BIN}" "${VALIDATOR}" "${root}" 2>&1)"
    status=$?
    if (( status == 0 )); then
        echo "失敗：${label}應被阻擋"
        failures=$((failures + 1))
        return
    fi
    if [[ "${output}" != *"${source_location} [Markdown 相對連結]"* ]]; then
        echo "失敗：${label}未回報 Markdown 來源位置"
        failures=$((failures + 1))
    fi
    if [[ "${output}" == *"Traceback"* || "${output}" == *"${root}"* ]]; then
        echo "失敗：${label}洩漏 traceback 或絕對路徑"
        failures=$((failures + 1))
    fi
}

# 驗證邊界異常只輸出安全規則，不洩漏 traceback 或測試絕對路徑。
expect_safe_failure() {
    local label="$1"
    local target_root="$2"
    local expected_rule="$3"
    local output
    local status

    output="$("${BASH_BIN}" "${VALIDATOR}" "${target_root}" 2>&1)"
    status=$?
    if (( status == 0 )); then
        echo "失敗：${label}應被阻擋"
        failures=$((failures + 1))
        return
    fi
    if [[ "${output}" != *"[${expected_rule}]"* ]]; then
        echo "失敗：${label}未命中預期規則"
        failures=$((failures + 1))
    fi
    if [[ "${output}" == *"Traceback"* || "${output}" == *"${TEST_ROOT}"* ]]; then
        echo "失敗：${label}洩漏 traceback 或測試絕對路徑"
        failures=$((failures + 1))
    fi
}

# 驗證非文字與連結邊界只回報安全規則，不回顯測試內容或路徑。
expect_sanitized_failure() {
    local label="$1"
    local target_root="$2"
    local expected_rule="$3"
    shift 3
    local output
    local status
    local forbidden

    output="$("${BASH_BIN}" "${VALIDATOR}" "${target_root}" 2>&1)"
    status=$?
    if (( status == 0 )); then
        echo "失敗：${label}應被阻擋"
        failures=$((failures + 1))
        return
    fi
    if [[ "${output}" != *"[${expected_rule}]"* ]]; then
        echo "失敗：${label}未命中預期規則"
        failures=$((failures + 1))
    fi
    for forbidden in "${target_root}" "${TEST_ROOT}" "$@"; do
        if [[ -n "${forbidden}" && "${output}" == *"${forbidden}"* ]]; then
            echo "失敗：${label}錯誤輸出洩漏測試內容或路徑"
            failures=$((failures + 1))
            break
        fi
    done
    if [[ "${output}" == *"Traceback"* ]]; then
        echo "失敗：${label}洩漏 traceback"
        failures=$((failures + 1))
    fi
}

# 每個負向情境使用獨立的暫存倉庫。
new_case() {
    local name="$1"
    local root="${TEST_ROOT}/${name}"

    create_valid_repo "${root}"
    printf '%s\n' "${root}"
}

valid_root="$(new_case valid-repo)"
expect_pass "正常倉庫" "${valid_root}"

safe_root="$(new_case safe-file)"
printf '%s\n' '# 公開說明' '' '這是不含敏感資訊的安全內容。' > "${safe_root}/SAFE.md"
expect_pass "安全檔案" "${safe_root}"

ordinary_key_suffix_root="$(new_case ordinary-key-suffix)"
printf '%s\n' 'monkey=ordinary_value_1234567890' 'turnkey=another_value_1234567890' > "${ordinary_key_suffix_root}/SAFE.md"
expect_pass "一般 key 字尾單字" "${ordinary_key_suffix_root}"

prefix_api_key_root="$(new_case prefixed-api-key)"
prefix_payload_one='PROVIDER_API_K''EY=provider_value_1234567890'
printf '%s\n' "${prefix_payload_one}" > "${prefix_api_key_root}/unsafe.txt"
expect_sanitized_failure \
    "帶前綴 API key" \
    "${prefix_api_key_root}" \
    "敏感賦值" \
    "${prefix_payload_one}" \
    "${prefix_payload_one#*=}"

prefix_token_root="$(new_case prefixed-token)"
prefix_payload_two='MY_PROVIDER_TO''KEN=provider_token_value_1234567890'
printf '%s\n' "${prefix_payload_two}" > "${prefix_token_root}/unsafe.txt"
expect_sanitized_failure \
    "多段前綴 token" \
    "${prefix_token_root}" \
    "敏感賦值" \
    "${prefix_payload_two}" \
    "${prefix_payload_two#*=}"

prefix_password_root="$(new_case prefixed-password)"
prefix_payload_three='SERVICE-PASS''WORD=provider_password_value_1234567890'
printf '%s\n' "${prefix_payload_three}" > "${prefix_password_root}/unsafe.txt"
expect_sanitized_failure \
    "帶前綴 password" \
    "${prefix_password_root}" \
    "敏感賦值" \
    "${prefix_payload_three}" \
    "${prefix_payload_three#*=}"

prefix_secret_root="$(new_case prefixed-secret)"
prefix_payload_four='PAYMENT_CLIENT_SEC''RET=provider_secret_value_1234567890'
printf '%s\n' "${prefix_payload_four}" > "${prefix_secret_root}/unsafe.txt"
expect_sanitized_failure \
    "多段前綴 secret" \
    "${prefix_secret_root}" \
    "敏感賦值" \
    "${prefix_payload_four}" \
    "${prefix_payload_four#*=}"

json_assignment_root="$(new_case json-sensitive-assignment)"
json_value_one='json_value_1234567890'
json_payload='{"api_k''ey": "'"${json_value_one}"'"}'
printf '%s\n' "${json_payload}" > "${json_assignment_root}/unsafe.json"
expect_sanitized_failure \
    "JSON 引號敏感鍵" \
    "${json_assignment_root}" \
    "敏感賦值" \
    "${json_payload}" \
    "${json_value_one}"

asset_assignment_root="$(new_case asset-input-sensitive-assignment)"
asset_value_one='asset_value_1234567890'
asset_payload='{{INPUT:PROVIDER_API_K''EY='"${asset_value_one}"'}}'
printf '%s\n' "${asset_payload}" >> "${asset_assignment_root}/skills/ai-development-workflow/assets/requirement-plan-template.md"
expect_sanitized_failure \
    "asset INPUT 內敏感賦值" \
    "${asset_assignment_root}" \
    "敏感賦值" \
    "${asset_payload}" \
    "${asset_value_one}"

invalid_utf8_root="$(new_case invalid-utf8)"
invalid_utf8_content='invalid_utf8_payload_marker_1234567890'
invalid_utf8_secret='sec''ret=invalid_utf8_value_1234567890'
printf '\377%s%s\n' "${invalid_utf8_content}" "${invalid_utf8_secret}" > "${invalid_utf8_root}/invalid.bin"
expect_sanitized_failure \
    "無效 UTF-8" \
    "${invalid_utf8_root}" \
    "UTF-8 文字" \
    "${invalid_utf8_content}" \
    "${invalid_utf8_secret}"

nul_root="$(new_case nul-content)"
nul_content='nul_payload_marker_1234567890'
nul_secret='sec''ret=nul_value_1234567890'
printf '%s\0%s\n' "${nul_content}" "${nul_secret}" > "${nul_root}/nul.bin"
expect_sanitized_failure \
    "NUL 內容" \
    "${nul_root}" \
    "非文字內容" \
    "${nul_content}" \
    "${nul_secret}"

utf16_root="$(new_case utf16-content)"
utf16_content='utf16_payload_marker_1234567890'
utf16_secret='sec''ret=utf16_value_1234567890'
{
    printf '\377\376'
    while IFS= read -r -n 1 character; do
        printf '%s\0' "${character}"
    done < <(printf '%s' "${utf16_content}${utf16_secret}")
} > "${utf16_root}/utf16.bin"
expect_sanitized_failure \
    "典型 UTF-16 內容" \
    "${utf16_root}" \
    "非文字內容" \
    "${utf16_content}" \
    "${utf16_secret}"

git_pointer_root="$(new_case git-pointer)"
git_pointer_path='/Users/'"example"'/workspace/.git/worktrees/publication'
printf '%s\n' "gitdir: ${git_pointer_path}" > "${git_pointer_root}/.git"
expect_pass ".git 指標檔" "${git_pointer_root}"

idea_root="$(new_case ignored-idea)"
mkdir -p "${idea_root}/.idea"
idea_path='/Users/'"example"'/workspace'
printf '%s\n' "last_opened_path=${idea_path}" > "${idea_root}/.idea/workspace.xml"
expect_pass "已忽略的 IDE 設定" "${idea_root}"

idea_link_root="$(new_case markdown-idea-link)"
mkdir -p "${idea_link_root}/.idea"
printf '%s\n' 'safe ignored content' > "${idea_link_root}/.idea/ignored.md"
printf '%s\n' '# 連結' '' '[IDE](.idea/ignored.md)' > "${idea_link_root}/LINKS.md"
expect_sanitized_failure \
    "Markdown 連向 .idea" \
    "${idea_link_root}" \
    "Markdown 排除目錄"

git_link_root="$(new_case markdown-git-link)"
mkdir -p "${git_link_root}/.git"
printf '%s\n' 'safe ignored content' > "${git_link_root}/.git/ignored.md"
printf '%s\n' '# 連結' '' '[Git](.git/ignored.md)' > "${git_link_root}/LINKS.md"
expect_sanitized_failure \
    "Markdown 連向 .git" \
    "${git_link_root}" \
    "Markdown 排除目錄"

excluded_symlink_root="$(new_case markdown-excluded-symlink)"
excluded_external_path="${TEST_ROOT}/outside-markdown-excluded.md"
excluded_external_content='outside_markdown_payload_1234567890'
excluded_external_secret='sec''ret=outside_markdown_value_1234567890'
printf '%s%s\n' "${excluded_external_content}" "${excluded_external_secret}" > "${excluded_external_path}"
mkdir -p "${excluded_symlink_root}/.idea"
ln -s "${excluded_external_path}" "${excluded_symlink_root}/.idea/outside.md"
printf '%s\n' '# 連結' '' '[外部](.idea/outside.md)' > "${excluded_symlink_root}/LINKS.md"
expect_sanitized_failure \
    "排除目錄 symlink 越界" \
    "${excluded_symlink_root}" \
    "Markdown 排除目錄" \
    "${excluded_external_path}" \
    "${excluded_external_content}" \
    "${excluded_external_secret}"

general_symlink_root="$(new_case general-symlink)"
general_external_path="${TEST_ROOT}/outside-general.txt"
general_external_content='sec''ret=outside_symlink_value_1234567890'
printf '%s\n' "${general_external_content}" > "${general_external_path}"
ln -s "${general_external_path}" "${general_symlink_root}/unsafe-link.txt"
expect_symlink_fail \
    "一般符號連結" \
    "${general_symlink_root}" \
    "unsafe-link.txt" \
    "${general_external_path}" \
    "${general_external_content}"

required_symlink_root="$(new_case required-symlink)"
required_skill_path="${required_symlink_root}/skills/ai-development-workflow/SKILL.md"
required_external_path="${TEST_ROOT}/outside-required-skill.md"
required_external_content='outside-required-skill-content'
mv "${required_skill_path}" "${required_external_path}"
printf '%s\n' "${required_external_content}" >> "${required_external_path}"
ln -s "${required_external_path}" "${required_skill_path}"
expect_symlink_fail \
    "必要檔案符號連結" \
    "${required_symlink_root}" \
    "skills/ai-development-workflow/SKILL.md" \
    "${required_external_path}" \
    "${required_external_content}"

directory_symlink_root="$(new_case directory-symlink)"
directory_external_path="${TEST_ROOT}/outside-directory"
directory_external_content='outside-directory-content'
mkdir -p "${directory_external_path}"
printf '%s\n' "${directory_external_content}" > "${directory_external_path}/content.txt"
ln -s "${directory_external_path}" "${directory_symlink_root}/linked-directory"
expect_symlink_fail \
    "目錄符號連結" \
    "${directory_symlink_root}" \
    "linked-directory" \
    "${directory_external_path}" \
    "${directory_external_content}"

asset_loop_root="$(new_case asset-loop-symlink)"
asset_loop_path="${asset_loop_root}/skills/ai-development-workflow/assets"
mv "${asset_loop_path}" "${TEST_ROOT}/outside-assets-backup"
ln -s 'assets' "${asset_loop_path}"
expect_safe_failure "assets 循環符號連結" "${asset_loop_root}" "符號連結"

root_symlink_target="$(new_case root-symlink-target)"
root_symlink_path="${TEST_ROOT}/root-symlink"
ln -s "${root_symlink_target}" "${root_symlink_path}"
expect_safe_failure "root 參數符號連結" "${root_symlink_path}" "目標根目錄符號連結"

root_symlink_slash_target="$(new_case root-symlink-slash-target)"
root_symlink_slash_path="${TEST_ROOT}/root-symlink-slash"
ln -s "${root_symlink_slash_target}" "${root_symlink_slash_path}"
expect_safe_failure "root 符號連結尾斜線" "${root_symlink_slash_path}/" "目標根目錄符號連結"

root_parent_target="${TEST_ROOT}/root-parent-target"
root_parent_repo="${root_parent_target}/repo"
mkdir -p "${root_parent_target}"
create_valid_repo "${root_parent_repo}"
root_parent_symlink="${TEST_ROOT}/root-parent-symlink"
ln -s "${root_parent_target}" "${root_parent_symlink}"
expect_safe_failure "root 父路徑含符號連結" "${root_parent_symlink}/repo" "目標根目錄符號連結"

private_key_root="$(new_case private-key)"
private_key_marker='-----BEGIN '"PRIVATE KEY"'-----'
printf '%s\n' "${private_key_marker}" > "${private_key_root}/unsafe.txt"
expect_fail "私鑰" "${private_key_root}" "私鑰" "${private_key_marker}"

key_root="$(new_case bare-key)"
key_value='publication_check_key_value_1234567890'
printf '%s\n' "ke""y=${key_value}" > "${key_root}/unsafe.txt"
expect_fail "裸 key 賦值" "${key_root}" "敏感賦值" "${key_value}"

secret_root="$(new_case secret)"
secret_value='publication_check_secret_value_1234567890'
printf '%s\n' "sec""ret=${secret_value}" > "${secret_root}/unsafe.txt"
expect_fail "secret 賦值" "${secret_root}" "敏感賦值" "${secret_value}"

password_root="$(new_case password)"
password_value='publication_check_password_value_1234567890'
printf '%s\n' "pass""word=${password_value}" > "${password_root}/unsafe.txt"
expect_fail "password 賦值" "${password_root}" "敏感賦值" "${password_value}"

token_root="$(new_case token)"
token_value='publication_check_token_value_1234567890'
printf '%s\n' "to""ken=${token_value}" > "${token_root}/unsafe.txt"
expect_fail "token 賦值" "${token_root}" "敏感賦值" "${token_value}"

github_pat_root="$(new_case github-pat)"
github_pat_value='github''_pat_publication_check_value_1234567890'
printf '%s\n' "${github_pat_value}" > "${github_pat_root}/unsafe.txt"
expect_fail "GitHub fine-grained 憑證" "${github_pat_root}" "GitHub 憑證" "${github_pat_value}"

github_ghp_root="$(new_case github-ghp)"
github_ghp_value='gh''p_publication_check_value_1234567890'
printf '%s\n' "${github_ghp_value}" > "${github_ghp_root}/unsafe.txt"
expect_fail "GitHub ghp 憑證" "${github_ghp_root}" "GitHub 憑證" "${github_ghp_value}"

aws_root="$(new_case aws-key)"
aws_value='AK''IA''1234567890ABCDEF'
printf '%s\n' "${aws_value}" > "${aws_root}/unsafe.txt"
expect_fail "AWS 憑證" "${aws_root}" "AWS 憑證" "${aws_value}"

email_root="$(new_case email)"
email_value='writer''@''example.invalid'
printf '%s\n' "${email_value}" > "${email_root}/unsafe.txt"
expect_fail "Email" "${email_root}"

phone_root="$(new_case phone)"
phone_value='09''12''345''678'
printf '%s\n' "${phone_value}" > "${phone_root}/unsafe.txt"
expect_fail "台灣手機" "${phone_root}"

internal_url_root="$(new_case internal-url)"
internal_url='https://service''.'"internal"'/v1'
printf '%s\n' "${internal_url}" > "${internal_url_root}/unsafe.txt"
expect_fail "內部 URL" "${internal_url_root}"

local_path_root="$(new_case local-path)"
local_path='/Users/'"example"'/workspace'
printf '%s\n' "${local_path}" > "${local_path_root}/unsafe.txt"
expect_fail "本機家目錄路徑" "${local_path_root}"

private_ip_root="$(new_case private-ip)"
private_ip='10''.''20''.''30''.''40'
printf '%s\n' "${private_ip}" > "${private_ip_root}/unsafe.txt"
expect_fail "私有 IP" "${private_ip_root}" "私有 IP" "${private_ip}"

todo_root="$(new_case todo-placeholder)"
todo_value='TO''DO: finish validation'
printf '%s\n' "${todo_value}" > "${todo_root}/unsafe.txt"
expect_fail "TODO 占位符" "${todo_root}" "開發占位符" "${todo_value}"

tbd_root="$(new_case tbd-placeholder)"
tbd_value='TB''D: validation detail'
printf '%s\n' "${tbd_value}" > "${tbd_root}/unsafe.txt"
expect_fail "TBD 占位符" "${tbd_root}" "開發占位符" "${tbd_value}"

bracket_todo_root="$(new_case bracket-todo-placeholder)"
bracket_todo_value='[TO''DO]'
printf '%s\n' "${bracket_todo_value}" > "${bracket_todo_root}/unsafe.txt"
expect_fail "方括號 TODO 占位符" "${bracket_todo_root}" "開發占位符" "${bracket_todo_value}"

replace_me_root="$(new_case replace-me-placeholder)"
replace_me_value='REPLACE''_ME'
printf '%s\n' "${replace_me_value}" > "${replace_me_root}/unsafe.txt"
expect_fail "REPLACE""_ME 占位符" "${replace_me_root}" "開發占位符" "${replace_me_value}"

language_root="$(new_case language)"
language_term='需求''计划'
printf '%s\n' "${language_term}" > "${language_root}/language.md"
expect_fail "簡體常見詞" "${language_root}"

invalid_frontmatter_root="$(new_case invalid-frontmatter)"
skill_file="${invalid_frontmatter_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: AI Development Workflow' \
    'description: Use when validating an invalid name.' \
    'license: example' \
    '---' \
    '# 無效範例' \
    > "${skill_file}"
expect_fail "無效 frontmatter" "${invalid_frontmatter_root}"

missing_description_root="$(new_case missing-description)"
skill_file="${missing_description_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: ai-development-workflow' \
    '---' \
    '# 缺少描述' \
    > "${skill_file}"
expect_fail "frontmatter 缺少 description" "${missing_description_root}" "frontmatter 欄位"

frontmatter_colon_root="$(new_case frontmatter-colon)"
skill_file="${frontmatter_colon_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: ai-development-workflow' \
    'description: Use when: invalid' \
    '---' \
    '# 無效純量' \
    > "${skill_file}"
expect_fail "frontmatter colon-space" "${frontmatter_colon_root}" "frontmatter 純量"

frontmatter_trailing_colon_root="$(new_case frontmatter-trailing-colon)"
skill_file="${frontmatter_trailing_colon_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: ai-development-workflow' \
    'description: Use when invalid:' \
    '---' \
    '# 行尾 colon' \
    > "${skill_file}"
expect_fail "frontmatter 行尾 colon" "${frontmatter_trailing_colon_root}" "frontmatter 純量"

frontmatter_quote_root="$(new_case frontmatter-unclosed-quote)"
skill_file="${frontmatter_quote_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: ai-development-workflow' \
    'description: "Use when the quote is unfinished.' \
    '---' \
    '# 未閉合引號' \
    > "${skill_file}"
expect_fail "frontmatter 未閉合引號" "${frontmatter_quote_root}" "frontmatter 純量"

frontmatter_multiline_root="$(new_case frontmatter-multiline)"
skill_file="${frontmatter_multiline_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: ai-development-workflow' \
    'description: |' \
    '  Use when a multiline value is requested.' \
    '---' \
    '# 多行語法' \
    > "${skill_file}"
expect_fail "frontmatter 多行語法" "${frontmatter_multiline_root}" "frontmatter 純量"

frontmatter_complex_root="$(new_case frontmatter-complex)"
skill_file="${frontmatter_complex_root}/skills/ai-development-workflow/SKILL.md"
printf '%s\n' \
    '---' \
    'name: ai-development-workflow' \
    'description: [Use when a complex value is requested]' \
    '---' \
    '# 複雜語法' \
    > "${skill_file}"
expect_fail "frontmatter 複雜語法" "${frontmatter_complex_root}" "frontmatter 純量"

openai_top_level_root="$(new_case openai-top-level)"
openai_file="${openai_top_level_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'display_name: "AI Development Workflow"' \
    'short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    'default_prompt: "使用 $ai-development-workflow 處理目前需求。"' \
    > "${openai_file}"
expect_fail "openai metadata 放在頂層" "${openai_top_level_root}" "interface 區塊"

openai_other_section_root="$(new_case openai-other-section)"
openai_file="${openai_other_section_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'metadata:' \
    '  display_name: "AI Development Workflow"' \
    '  short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    '  default_prompt: "使用 $ai-development-workflow 處理目前需求。"' \
    > "${openai_file}"
expect_fail "openai metadata 放在其他區塊" "${openai_other_section_root}" "interface 區塊"

openai_missing_field_root="$(new_case openai-missing-field)"
openai_file="${openai_missing_field_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'interface:' \
    '  display_name: "AI Development Workflow"' \
    '  short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    > "${openai_file}"
expect_fail "openai metadata 缺少必要欄位" "${openai_missing_field_root}" "default_prompt"

openai_unclosed_quote_root="$(new_case openai-unclosed-quote)"
openai_file="${openai_unclosed_quote_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'interface:' \
    '  display_name: "AI Development Workflow"' \
    '  short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    '  default_prompt: "使用 $ai-development-workflow 處理目前需求。' \
    > "${openai_file}"
expect_fail "openai.yaml 未閉合引號" "${openai_unclosed_quote_root}" "openai.yaml 字串"

openai_tab_indent_root="$(new_case openai-tab-indent)"
openai_file="${openai_tab_indent_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'interface:' \
    $'\tdisplay_name: "AI Development Workflow"' \
    $'\tshort_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    $'\tdefault_prompt: "使用 $ai-development-workflow 處理目前需求。"' \
    > "${openai_file}"
expect_fail "openai.yaml tab 縮排" "${openai_tab_indent_root}" "openai.yaml 結構"

openai_invalid_line_root="$(new_case openai-invalid-line)"
openai_file="${openai_invalid_line_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'interface:' \
    '  display_name: "AI Development Workflow"' \
    '  invalid metadata line' \
    '  short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    '  default_prompt: "使用 $ai-development-workflow 處理目前需求。"' \
    > "${openai_file}"
expect_fail "openai.yaml 無法解析行" "${openai_invalid_line_root}" "openai.yaml 結構"

openai_duplicate_key_root="$(new_case openai-duplicate-key)"
openai_file="${openai_duplicate_key_root}/skills/ai-development-workflow/agents/openai.yaml"
printf '%s\n' \
    'interface:' \
    '  display_name: "AI Development Workflow"' \
    '  display_name: "AI Development Workflow"' \
    '  short_description: "建立完整且可驗證的 AI 開發工作流程與清楚審查步驟"' \
    '  default_prompt: "使用 $ai-development-workflow 處理目前需求。"' \
    > "${openai_file}"
expect_fail "openai.yaml 重複 metadata key" "${openai_duplicate_key_root}" "openai.yaml 重複欄位"

invalid_link_root="$(new_case invalid-link)"
printf '%s\n' '# 連結' '' '[失效連結](missing-file.md#section)' > "${invalid_link_root}/LINKS.md"
expect_fail "失效相對連結" "${invalid_link_root}"

valid_reference_root="$(new_case valid-reference-link)"
printf '%s\n' \
    '# Reference 連結' \
    '' \
    '[相對文件][guide]' \
    '[外部文件][web]' \
    '[本頁章節][local]' \
    '' \
    '[guide]: skills/ai-development-workflow/references/examples.md#虛構範例' \
    '[web]: https://example.invalid/guide' \
    '[local]: #reference-連結' \
    > "${valid_reference_root}/REFERENCES.md"
expect_pass "有效 reference-style 連結" "${valid_reference_root}"

invalid_reference_target_root="$(new_case invalid-reference-target)"
printf '%s\n' \
    '# Reference 連結' \
    '' \
    '[失效文件][missing]' \
    '' \
    '[missing]: missing-reference.md#section' \
    > "${invalid_reference_target_root}/REFERENCES.md"
expect_fail "reference-style 失效 target" "${invalid_reference_target_root}" "Markdown 相對連結"

undefined_reference_root="$(new_case undefined-reference)"
printf '%s\n' '# Reference 連結' '' '[未定義連結][unknown]' > "${undefined_reference_root}/REFERENCES.md"
expect_fail "reference-style 未定義 ref" "${undefined_reference_root}" "Markdown reference 未定義"

markdown_loop_root="$(new_case markdown-loop)"
ln -s 'loop-b' "${markdown_loop_root}/loop-a"
ln -s 'loop-a' "${markdown_loop_root}/loop-b"
printf '%s\n' '# 循環連結' '' '[連結](loop-a)' > "${markdown_loop_root}/LOOP.md"
expect_markdown_loop_fail "Markdown 循環符號連結" "${markdown_loop_root}" "LOOP.md:3"

missing_structure_root="$(new_case missing-structure)"
rm "${missing_structure_root}/skills/ai-development-workflow/references/examples.md"
expect_fail "缺少必要結構" "${missing_structure_root}"

missing_heading_root="$(new_case missing-heading)"
heading_file="${missing_heading_root}/skills/ai-development-workflow/assets/requirement-plan-template.md"
sed -i.bak 's/^## 風險$/## 無風險資料/' "${heading_file}"
rm "${heading_file}.bak"
expect_fail "需求範本缺少必要章節" "${missing_heading_root}" "範本必填章節"

missing_test_heading_root="$(new_case missing-test-heading)"
heading_file="${missing_test_heading_root}/skills/ai-development-workflow/assets/test-design-template.md"
sed -i.bak 's/^## 回歸$/## 無回歸資料/' "${heading_file}"
rm "${heading_file}.bak"
expect_fail "測試範本缺少必要章節" "${missing_test_heading_root}" "範本必填章節"

pythonless_root="$(new_case pythonless)"
pythonless_bin="${TEST_ROOT}/pythonless-bin"
mkdir -p "${pythonless_bin}"
ln -s "$(command -v dirname)" "${pythonless_bin}/dirname"
pythonless_output="$(PATH="${pythonless_bin}" "${BASH_BIN}" "${VALIDATOR}" "${pythonless_root}" 2>&1)"
pythonless_status=$?
if (( pythonless_status != 1 )); then
    echo "失敗：缺少 python3 時應以 exit 1 結束"
    failures=$((failures + 1))
fi

validator_source="$(<"${VALIDATOR}")"
walk_handler_signature='def handle_''walk_error(error: OSError) -> None:'
walk_call='os.walk(root, onerror=handle_''walk_error)'
if [[ "${validator_source}" != *"${walk_handler_signature}"* || "${validator_source}" != *"${walk_call}"* ]]; then
    echo "失敗：all_files 應使用具名 onerror handler"
    failures=$((failures + 1))
fi

if (( EUID == 0 )); then
    echo "略過：root 環境無法可靠驗證不可讀目錄"
else
    unreadable_root="$(new_case unreadable-directory)"
    mkdir -p "${unreadable_root}/locked"
    chmod 000 "${unreadable_root}/locked"
    expect_fail "不可讀目錄" "${unreadable_root}" "目錄讀取"
    chmod 700 "${unreadable_root}/locked"
fi
if [[ "${pythonless_output}" != *"python3"* ]]; then
    echo "失敗：缺少 python3 時應輸出明確說明"
    failures=$((failures + 1))
fi

allowlist_root="$(new_case language-allowlist)"
allowlist_term='代码''审查'
printf '%s\n' "${allowlist_term}" > "${allowlist_root}/external-contract.md"
printf '%s|%s\n' 'external-contract.md' "${allowlist_term}" > "${allowlist_root}/.publication-language-allowlist"
expect_pass "語言 allowlist" "${allowlist_root}"

allowlist_secret='sk''-publication_check_value_12345678901234567890'
printf '%s\n' "api""_key=${allowlist_secret}" >> "${allowlist_root}/external-contract.md"
expect_fail "allowlist 不得放行敏感資訊" "${allowlist_root}"

allowlist_loop_root="$(new_case allowlist-loop-symlink)"
ln -s 'allowlist-loop-b.md' "${allowlist_loop_root}/allowlist-loop-a.md"
ln -s 'allowlist-loop-a.md' "${allowlist_loop_root}/allowlist-loop-b.md"
allowlist_loop_term='代码''审查'
printf '%s|%s\n' 'allowlist-loop-a.md' "${allowlist_loop_term}" > "${allowlist_loop_root}/.publication-language-allowlist"
expect_safe_failure "allowlist 循環符號連結" "${allowlist_loop_root}" "語言 allowlist 路徑"

if (( failures > 0 )); then
    echo "失敗：${failures} 個發布檢查測試未通過"
    exit 1
fi

echo "通過：發布檢查測試全數通過"
