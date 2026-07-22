#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_ROOT="${1:-${REPO_ROOT}}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "錯誤：python3 [執行環境]"
    exit 1
fi

ROOT_LINK_CHECK="${TARGET_ROOT}"
while [[ "${ROOT_LINK_CHECK}" != "/" && "${ROOT_LINK_CHECK}" == */ ]]; do
    ROOT_LINK_CHECK="${ROOT_LINK_CHECK%/}"
done
if [[ -L "${ROOT_LINK_CHECK}" ]]; then
    echo "錯誤：. [目標根目錄符號連結]"
    exit 1
fi

if [[ ! -d "${TARGET_ROOT}" ]]; then
    echo "錯誤：. [目標目錄]"
    exit 1
fi

python3 - "${TARGET_ROOT}" <<'PY'
from __future__ import annotations

import ipaddress
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


root = Path(os.path.abspath(sys.argv[1]))


def root_has_symlink(path: Path) -> bool:
    """Check every lexical root component with lstat without following targets."""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            metadata = os.lstat(current)
        except OSError:
            print("錯誤：. [目標根目錄檢查]")
            sys.exit(1)
        if stat.S_ISLNK(metadata.st_mode):
            return True
    return False


if root_has_symlink(root):
    print("錯誤：. [目標根目錄符號連結]")
    sys.exit(1)

skill_name = "ai-development-workflow"
root_skill = root / "SKILL.md"
skill_root = root if root_skill.exists() or root_skill.is_symlink() else root / "skills" / skill_name
errors: set[tuple[str, str, int | None]] = set()


def relative(path: Path) -> str:
    """Return a stable path relative to the validation root."""
    try:
        value = path.relative_to(root)
    except ValueError:
        value = Path(path.name)
    return value.as_posix() or "."


def add_error(path: Path, rule: str, line: int | None = None) -> None:
    """Record an error without retaining matched file content."""
    errors.add((relative(path), rule, line))


def read_text(path: Path) -> str:
    """Read strict UTF-8 text and reject binary-like content without echoing it."""
    if path.is_symlink():
        add_error(path, "符號連結")
        return ""
    try:
        raw = path.read_bytes()
    except OSError:
        add_error(path, "檔案讀取")
        return ""
    if b"\x00" in raw:
        add_error(path, "非文字內容")
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        add_error(path, "UTF-8 文字")
        return ""


def line_number(text: str, offset: int) -> int:
    """Convert a character offset to a one-based line number."""
    return text.count("\n", 0, offset) + 1


required_files = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/requirement-plan.md",
    "references/test-design.md",
    "references/git-diff-review.md",
    "references/examples.md",
    "assets/requirement-plan-template.md",
    "assets/test-design-template.md",
]
for required in required_files:
    candidate = skill_root / required
    if candidate.is_symlink():
        add_error(candidate, "符號連結")
    elif not candidate.is_file():
        add_error(candidate, "必要結構")


def parse_frontmatter_scalar(value: str) -> str | None:
    """Parse the strict plain or JSON-quoted frontmatter scalar subset."""
    value = value.strip()
    if not value:
        return ""
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None
        return parsed if isinstance(parsed, str) else None
    if value.startswith("'") or value[0] in "-?:,[]{}#&*!|>'%@`":
        return None
    if re.search(r":(?:\s|$)", value) or " #" in value:
        return None
    return value


def parse_double_quoted_string(value: str) -> str | None:
    """Parse a YAML double-quoted string through the compatible JSON subset."""
    value = value.strip()
    if len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
        return None
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, str) else None


def validate_frontmatter(path: Path) -> None:
    """Validate the constrained SKILL frontmatter contract."""
    if path.is_symlink() or not path.is_file():
        return
    text = read_text(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        add_error(path, "frontmatter", 1)
        return
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        add_error(path, "frontmatter", 1)
        return

    values: dict[str, str] = {}
    key_lines: dict[str, int] = {}
    malformed = False
    for index, raw_line in enumerate(lines[1:closing], start=2):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)", raw_line)
        if not match:
            add_error(path, "frontmatter", index)
            malformed = True
            continue
        key, raw_value = match.groups()
        if key in values:
            add_error(path, "frontmatter 重複欄位", index)
            malformed = True
        parsed_value = parse_frontmatter_scalar(raw_value)
        if parsed_value is None:
            add_error(path, "frontmatter 純量", index)
            malformed = True
            parsed_value = ""
        values[key] = parsed_value
        key_lines[key] = index

    if malformed or set(values) != {"name", "description"}:
        add_error(path, "frontmatter 欄位", 1)
    name = values.get("name", "")
    if name != skill_name or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None:
        add_error(path, "Skill 名稱", key_lines.get("name", 1))
    description = values.get("description", "")
    if not description or not description.startswith("Use when"):
        add_error(path, "Skill 描述", key_lines.get("description", 1))


def interface_yaml_values(path: Path) -> tuple[bool, dict[str, str], dict[str, int]]:
    """Parse the strict OpenAI metadata YAML subset."""
    values: dict[str, str] = {}
    lines: dict[str, int] = {}
    if path.is_symlink() or not path.is_file():
        return False, values, lines
    source_lines = read_text(path).splitlines()
    allowed_keys = {"display_name", "short_description", "default_prompt"}
    has_interface = False
    for index, raw_line in enumerate(source_lines, start=1):
        if "\t" in raw_line:
            add_error(path, "openai.yaml 結構", index)
            continue
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line == "interface:":
            if has_interface:
                add_error(path, "openai.yaml 結構", index)
            has_interface = True
            continue
        match = re.fullmatch(r"  ([a-z_][a-z0-9_]*): *(.*)", raw_line)
        if not match:
            add_error(path, "openai.yaml 結構", index)
            continue
        key, raw_value = match.groups()
        if not has_interface or key not in allowed_keys:
            add_error(path, "openai.yaml 結構", index)
            continue
        if key in values:
            add_error(path, "openai.yaml 重複欄位", index)
            continue
        values[key] = raw_value.strip()
        lines[key] = index
    return has_interface, values, lines


def validate_openai_yaml(path: Path) -> None:
    """Validate required OpenAI interface metadata."""
    has_interface, values, lines = interface_yaml_values(path)
    if not has_interface:
        add_error(path, "interface 區塊", 1)
    parsed_values: dict[str, str] = {}
    for key in ("display_name", "short_description", "default_prompt"):
        if key not in values:
            continue
        parsed = parse_double_quoted_string(values[key])
        if parsed is None:
            add_error(path, "openai.yaml 字串", lines.get(key, 1))
            continue
        parsed_values[key] = parsed
    display_name = parsed_values.get("display_name", "")
    short_description = parsed_values.get("short_description", "")
    default_prompt = parsed_values.get("default_prompt", "")
    if not display_name:
        add_error(path, "display_name", lines.get("display_name", 1))
    if not 25 <= len(short_description) <= 64:
        add_error(path, "short_description 長度", lines.get("short_description", 1))
    if "$ai-development-workflow" not in default_prompt:
        add_error(path, "default_prompt", lines.get("default_prompt", 1))


validate_frontmatter(skill_root / "SKILL.md")
validate_openai_yaml(skill_root / "agents" / "openai.yaml")


def handle_walk_error(error: OSError) -> None:
    """Record directory traversal failures without exposing exception details."""
    failed_path = Path(error.filename) if error.filename else root
    if not failed_path.is_absolute():
        failed_path = root / failed_path
    add_error(failed_path, "目錄讀取")


def all_files() -> list[Path]:
    """List every working-tree file while excluding only Git metadata."""
    found: list[Path] = []
    for current, directories, filenames in os.walk(root, onerror=handle_walk_error):
        retained_directories: list[str] = []
        for name in sorted(directories):
            if name in {".git", ".idea"}:
                continue
            path = Path(current) / name
            if path.is_symlink():
                add_error(path, "符號連結")
                continue
            retained_directories.append(name)
        directories[:] = retained_directories
        for filename in sorted(filenames):
            if filename == ".git":
                continue
            path = Path(current) / filename
            if path.is_symlink():
                add_error(path, "符號連結")
                continue
            if path.is_file():
                found.append(path)
    return found


files = all_files()


def markdown_without_fenced_code(text: str) -> str:
    """Mask fenced code so example syntax is not mistaken for a link."""
    output: list[str] = []
    fence: str | None = None
    for raw_line in text.splitlines(keepends=True):
        match = re.match(r"^\s*(```+|~~~+)", raw_line)
        if match:
            marker = match.group(1)[0]
            fence = None if fence == marker else marker if fence is None else fence
            output.append("\n" if raw_line.endswith("\n") else "")
        elif fence is None:
            output.append(
                re.sub(r"(`+).*?\1", lambda match: " " * len(match.group(0)), raw_line)
            )
        else:
            output.append("\n" if raw_line.endswith("\n") else "")
    return "".join(output)


link_pattern = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
reference_use_pattern = re.compile(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]")
reference_definition_pattern = re.compile(
    r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:\s*(?:<([^>\n]+)>|(\S+))"
)


def normalize_reference(label: str) -> str:
    """Normalize a Markdown reference label for case-insensitive lookup."""
    return " ".join(label.split()).casefold()


def validate_markdown_target(
    path: Path,
    text: str,
    target: str,
    offset: int,
    is_asset: bool,
) -> None:
    """Validate a Markdown target while allowing public and local anchors."""
    lowered = target.lower()
    if is_asset and "{{INPUT:" in target:
        return
    if not target or target.startswith("#") or lowered.startswith(("http://", "https://", "mailto:")):
        return
    path_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path_part:
        return
    lexical_linked = Path(os.path.abspath(path.parent / path_part))
    try:
        lexical_relative = lexical_linked.relative_to(root)
    except ValueError:
        add_error(path, "Markdown 相對連結", line_number(text, offset))
        return
    if any(part in {".git", ".idea"} for part in lexical_relative.parts):
        add_error(path, "Markdown 排除目錄", line_number(text, offset))
        return
    try:
        linked = lexical_linked.resolve(strict=True)
        linked.relative_to(root)
    except (RuntimeError, OSError, ValueError):
        add_error(path, "Markdown 相對連結", line_number(text, offset))
        return


for path in files:
    if path.suffix.lower() not in {".md", ".markdown"}:
        continue
    text = markdown_without_fenced_code(read_text(path))
    try:
        path.relative_to(skill_root / "assets")
        is_asset = True
    except ValueError:
        is_asset = False
    for match in link_pattern.finditer(text):
        raw_target = match.group(1).strip()
        if raw_target.startswith("<") and ">" in raw_target:
            target = raw_target[1:raw_target.index(">")]
        else:
            target = raw_target.split(maxsplit=1)[0]
        validate_markdown_target(path, text, target, match.start(), is_asset)

    definitions: dict[str, tuple[str, int]] = {}
    for match in reference_definition_pattern.finditer(text):
        label = normalize_reference(match.group(1))
        target = match.group(2) or match.group(3) or ""
        definitions.setdefault(label, (target, match.start()))
        validate_markdown_target(path, text, target, match.start(), is_asset)
    for match in reference_use_pattern.finditer(text):
        line_start = text.rfind("\n", 0, match.start()) + 1
        if re.fullmatch(r"\s*#{1,6}\s*", text[line_start:match.start()]):
            continue
        label = normalize_reference(match.group(2) or match.group(1))
        if label not in definitions:
            add_error(path, "Markdown reference 未定義", line_number(text, match.start()))


def headings(path: Path) -> list[str]:
    """Extract normalized Markdown heading text."""
    if not path.is_file():
        return []
    result: list[str] = []
    for raw_line in read_text(path).splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", raw_line)
        if match:
            result.append(match.group(1).strip())
    return result


def validate_headings(path: Path, required: list[str]) -> None:
    """Require each publication template section by visible heading text."""
    present = headings(path)
    for expected in required:
        if not any(heading == expected or heading.startswith(expected + "／") for heading in present):
            add_error(path, "範本必填章節")


def markdown_section(path: Path, heading: str) -> str:
    """Return one level-two Markdown section without including later peers."""
    if not path.is_file():
        return ""
    lines = read_text(path).splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = index + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^#{1,2}\s+", lines[index]):
            end = index
            break
    return markdown_without_fenced_code("\n".join(lines[start:end]))


def validate_required_fields(
    path: Path,
    section_heading: str,
    subsection_headings: list[str],
    fields: list[str],
    rule: str,
) -> None:
    """Require exact subsection headings and field labels within one section."""
    section = markdown_section(path, section_heading)
    if not section:
        return
    section_lines = section.splitlines()
    for expected in subsection_headings:
        if f"### {expected}" not in section_lines:
            add_error(path, rule)
    for expected in fields:
        pattern = re.compile(rf"^- {re.escape(expected)}：")
        if not any(pattern.match(line) for line in section_lines):
            add_error(path, rule)


validate_headings(
    skill_root / "assets" / "requirement-plan-template.md",
    [
        "基本資訊",
        "需求來源與目標",
        "範圍與非範圍",
        "現況與證據",
        "影響分析",
        "複用分析",
        "方案與決策",
        "風險",
        "檔案級實作計畫",
        "實作清單",
        "測試與驗證",
        "文件改動",
        "待確認事項",
        "變更紀錄",
        "實作與驗證結果",
        "AI 協作紀錄與成效",
    ],
)
validate_required_fields(
    skill_root / "assets" / "requirement-plan-template.md",
    "AI 協作紀錄與成效",
    [
        "可驗證貢獻",
        "效率量化",
    ],
    [
        "需求規模",
        "協作範圍",
        "產出與驗證",
        "提前發現與避免返工",
        "人工決策與介入",
        "人工基準工時",
        "實際人工投入",
        "比較前提",
        "節省工時",
        "AI 協作工時節省率",
        "歸因限制",
        "計算口徑",
    ],
    "AI 提效欄位",
)
validate_headings(
    skill_root / "assets" / "test-design-template.md",
    [
        "基本資訊／關聯",
        "範圍與策略",
        "環境與依賴",
        "測試資料策略",
        "詳細情境",
        "目標自動化映射",
        "手動驗證與可選唯讀 SQL",
        "回歸",
        "交付測試清單",
        "自動化測試實施結果",
        "偏差與剩餘風險",
    ],
)


language_terms = [
    "需求" + "计划",
    "测试" + "设计",
    "代码" + "审查",
    "实现" + "计划",
    "项" + "目",
    "仓" + "库",
    "文" + "档",
    "复用" + "分析",
    "风" + "险",
    "影响" + "分析",
    "场" + "景",
    "优先" + "级",
    "响应" + "时间",
]


def load_language_allowlist(path: Path) -> set[tuple[str, str]]:
    """Load relative-path and term pairs used only by the language rule."""
    allowed: set[tuple[str, str]] = set()
    if path.is_symlink() or not path.is_file():
        return allowed
    for index, raw_line in enumerate(read_text(path).splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            add_error(path, "語言 allowlist 格式", index)
            continue
        raw_relative, term = (part.strip() for part in line.split("|", 1))
        candidate = Path(os.path.abspath(root / raw_relative))
        try:
            normalized = candidate.relative_to(root).as_posix()
        except ValueError:
            add_error(path, "語言 allowlist 路徑", index)
            continue
        if not raw_relative or not term:
            add_error(path, "語言 allowlist 格式", index)
            continue
        current = root
        has_symlink = False
        for part in Path(normalized).parts:
            current = current / part
            if current.is_symlink():
                has_symlink = True
                break
        try:
            is_file = candidate.is_file()
        except OSError:
            is_file = False
        if has_symlink or not is_file:
            add_error(path, "語言 allowlist 路徑", index)
            continue
        allowed.add((normalized, term))
    return allowed


allowlist_path = root / ".publication-language-allowlist"
language_allowlist = load_language_allowlist(allowlist_path)

private_key_pattern = re.compile(
    "-----BEGIN " + r"(?:RSA |EC |OPENSSH |DSA )?" + "PRIVATE KEY-----",
    re.IGNORECASE,
)
assignment_pattern = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"(?P<assignment_key_quote>[\"'])?"
    r"(?:[A-Za-z0-9]+[_-])*"
    r"(?:key|api[_-]?(?:key|token)|access[_-]?token|auth[_-]?token|token|password|passwd|pwd|secret|client[_-]?secret)"
    r"(?(assignment_key_quote)(?P=assignment_key_quote))"
    r"(?![A-Za-z0-9_-])"
    r"\s*[:=]\s*[\"']?[^\s\"'`]{8,}",
    re.IGNORECASE,
)
github_pattern = re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}\b")
aws_pattern = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
email_pattern = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b")
phone_pattern = re.compile(r"(?<!\d)09\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)")
url_pattern = re.compile(r"https?://[^\s<>()\]}'\"]+", re.IGNORECASE)
ipv4_pattern = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
home_path_patterns = [
    re.compile(r"/Users/[A-Za-z0-9._-]+(?:/|\b)"),
    re.compile(r"/home/[A-Za-z0-9._-]+(?:/|\b)"),
    re.compile(r"\bC:\\Users\\[A-Za-z0-9._-]+(?:\\|\b)", re.IGNORECASE),
]
placeholder_patterns = [
    re.compile("TO" + "DO:"),
    re.compile("TB" + "D:"),
    re.compile(r"\[" + "TO" + r"DO\]"),
    re.compile("REPLACE" + "_ME"),
]


def is_private_url(raw_url: str) -> bool:
    """Identify URLs that reveal local or private network locations."""
    try:
        hostname = (urlsplit(raw_url).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    if hostname == "localhost" or hostname.endswith((".internal", ".local", ".corp")):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


security_patterns = [
    ("私鑰", private_key_pattern),
    ("敏感賦值", assignment_pattern),
    ("GitHub 憑證", github_pattern),
    ("AWS 憑證", aws_pattern),
    ("Email", email_pattern),
    ("台灣手機", phone_pattern),
]

for path in files:
    text = read_text(path)
    rel = relative(path)
    if path != allowlist_path:
        for term in language_terms:
            if (rel, term) in language_allowlist:
                continue
            start = 0
            while True:
                offset = text.find(term, start)
                if offset < 0:
                    break
                add_error(path, "簡體常見詞", line_number(text, offset))
                start = offset + len(term)

    security_text = text
    placeholder_text = text
    asset_root = skill_root / "assets"
    try:
        path.relative_to(asset_root)
        placeholder_text = re.sub(r"\{\{INPUT:[^}\n]+\}\}", "", placeholder_text)
    except ValueError:
        pass

    for rule, pattern in security_patterns:
        for match in pattern.finditer(security_text):
            add_error(path, rule, line_number(security_text, match.start()))
    for match in url_pattern.finditer(security_text):
        if is_private_url(match.group(0)):
            add_error(path, "內部 URL", line_number(security_text, match.start()))
    for match in ipv4_pattern.finditer(security_text):
        try:
            address = ipaddress.ip_address(match.group(0))
        except ValueError:
            continue
        if address.is_private or address.is_loopback or address.is_link_local:
            add_error(path, "私有 IP", line_number(security_text, match.start()))
    for pattern in home_path_patterns:
        for match in pattern.finditer(security_text):
            add_error(path, "本機家目錄路徑", line_number(security_text, match.start()))
    for pattern in placeholder_patterns:
        for match in pattern.finditer(placeholder_text):
            add_error(path, "開發占位符", line_number(placeholder_text, match.start()))


if errors:
    for path, rule, line in sorted(errors, key=lambda item: (item[0], item[2] or 0, item[1])):
        suffix = f":{line}" if line is not None else ""
        print(f"錯誤：{path}{suffix} [{rule}]")
    sys.exit(1)

print("通過：發布檢查 PASS")
PY
