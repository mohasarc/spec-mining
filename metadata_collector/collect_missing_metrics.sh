#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./collect_missing_metrics.sh final_projects.csv out_metrics.csv
#
# Input CSV format (one entry per line; header allowed):
#   owner/repo,sha
# Example:
#   0HugoHu/HugoHu-Python-PySpark,57848da
#
# Output columns:
#   project,owner,repo,sha,url,sloc,stars,age_years,commit_count,stmt_cov_pct,branch_cov_pct,notes
#
# Extra per-project requirements (optional):
#   Put them next to this script:
#     ./requirements/<OWNER>-<REPO>_<SHA>/requirements.txt
#
# Env knobs:
#   WORKDIR=./_collect_workdir
#   TIMEOUT_TESTS_SEC=1500
#   TIMEOUT_CLONE_SEC=600
#   EXTRA_REQ_ROOT=/path/to/requirements   (defaults to <script_dir>/requirements)

INPUT_CSV="${1:-final_projects.csv}"
OUT_CSV="${2:-collected_missing_metrics.csv}"

WORKDIR="${WORKDIR:-./_collect_workdir}"
TIMEOUT_TESTS_SEC="${TIMEOUT_TESTS_SEC:-1500}"
TIMEOUT_CLONE_SEC="${TIMEOUT_CLONE_SEC:-600}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXTRA_REQ_ROOT="${EXTRA_REQ_ROOT:-${SCRIPT_DIR}/requirements}"

mkdir -p "$WORKDIR"

# ---------------- Helpers ----------------

have_cmd() { command -v "$1" >/dev/null 2>&1; }

safe_csv() {
  local s="${1:-}"
  s="${s//\"/\"\"}"
  printf "\"%s\"" "$s"
}

json_get() {
  local json="$1"
  local expr="$2"
  if have_cmd jq; then
    echo "$json" | jq -r "$expr"
  else
    echo ""
  fi
}

fetch_repo_json() {
  local owner="$1"
  local repo="$2"
  if have_cmd gh; then
    gh api "repos/${owner}/${repo}" 2>/dev/null || true
  else
    curl -sS -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/${owner}/${repo}" || true
  fi
}

age_years_from_created_at() {
  local created_at="$1"
  if [ -z "$created_at" ]; then
    echo ""
    return
  fi
  python3 - <<'PY' "$created_at"
import sys, datetime
s = sys.argv[1].strip()
try:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.datetime.fromisoformat(s)
    now = datetime.datetime.now(datetime.timezone.utc)
    age_years = (now - dt).total_seconds() / (365.25 * 24 * 3600)
    print(f"{age_years:.1f}")
except Exception:
    print("")
PY
}

compute_sloc() {
  local repo_dir="$1"
  if ! have_cmd cloc; then
    echo ""
    return
  fi
  local out
  out="$(cloc --json --quiet "$repo_dir" 2>/dev/null || true)"
  if [ -z "$out" ]; then
    echo ""
    return
  fi
  python3 - <<'PY' "$out"
import sys, json
try:
    data = json.loads(sys.argv[1])
    v = data.get("SUM", {}).get("code", 0)
    print(int(v) if v else "")
except Exception:
    print("")
PY
}

compute_commit_count() {
  local repo_dir="$1"
  (cd "$repo_dir" && git rev-list --count HEAD 2>/dev/null) || echo ""
}

compute_coverage() {
  # Returns: "<stmt_pct> <branch_pct>" or " " (both empty)
  local repo_dir="$1"
  local timeout_sec="$2"
  local owner="$3"
  local repo="$4"
  local sha="$5"

  local venv_dir="${repo_dir}/.cov_venv"
  rm -rf "$venv_dir" || true

  python3 -m venv "$venv_dir" >/dev/null 2>&1 || { echo " "; return; }
  # shellcheck disable=SC1090
  source "${venv_dir}/bin/activate"

  python -m pip install -q --upgrade pip >/dev/null 2>&1 || true
  python -m pip install -q pytest pytest-cov >/dev/null 2>&1 || { deactivate || true; echo " "; return; }

  # Install dependencies from root *.txt (best-effort)
  for f in "$repo_dir"/*.txt; do
    [ -f "$f" ] || continue
    python -m pip install -q -r "$f" >/dev/null 2>&1 || true
  done

  # Install extra per-project requirements if present
  local extra_req="${EXTRA_REQ_ROOT}/${owner}-${repo}_${sha}/requirements.txt"
  if [ -f "$extra_req" ]; then
    python -m pip install -q -r "$extra_req" >/dev/null 2>&1 || true
  fi

  # Install package (best-effort)
  if [ -f "$repo_dir/myInstall.sh" ]; then
    (cd "$repo_dir" && bash ./myInstall.sh) >/dev/null 2>&1 || true
  else
    (cd "$repo_dir" && python -m pip install -q ".[dev,test,tests,testing]") >/dev/null 2>&1 || true
  fi

  (cd "$repo_dir" && rm -f coverage.xml .coverage >/dev/null 2>&1 || true)

  local cmd=(pytest --continue-on-collection-errors --maxfail=1
             --cov=. --cov-branch --cov-report=xml:coverage.xml)

  if timeout -k 9 "${timeout_sec}" bash -lc "cd \"${repo_dir}\" && ${cmd[*]}" >/dev/null 2>&1; then
    :
  else
    deactivate || true
    rm -rf "$venv_dir" || true
    echo " "
    return
  fi

  local cov_xml="${repo_dir}/coverage.xml"
  if [ ! -f "$cov_xml" ]; then
    deactivate || true
    rm -rf "$venv_dir" || true
    echo " "
    return
  fi

  local parsed
  parsed="$(python3 - <<'PY' "$cov_xml"
import sys, xml.etree.ElementTree as ET
p = sys.argv[1]
try:
    root = ET.parse(p).getroot()
    line_rate = root.attrib.get("line-rate")
    branch_rate = root.attrib.get("branch-rate")
    def pct(x):
        if not x: return ""
        try: return f"{float(x)*100:.1f}"
        except Exception: return ""
    print(pct(line_rate), pct(branch_rate))
except Exception:
    print("", "")
PY
)"

  deactivate || true
  rm -rf "$venv_dir" || true
  echo "$parsed"
}

# ---------------- Output header ----------------
echo "project,owner,repo,sha,url,sloc,stars,age_years,commit_count,stmt_cov_pct,branch_cov_pct,notes" > "$OUT_CSV"

# ---------------- Main loop ----------------
tail -n +1 "$INPUT_CSV" | while IFS= read -r line || [ -n "$line" ]; do
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  [ -z "$line" ] && continue

  # skip header-ish lines
  if echo "$line" | grep -qiE '^(project|owner|repo|sha)'; then
    continue
  fi

  # Parse: owner/repo,sha
  owner_repo="${line%%,*}"
  sha="${line#*,}"

  # If there's no comma, skip
  if [ "$owner_repo" = "$line" ]; then
    continue
  fi

  owner_repo="${owner_repo// /}"
  sha="${sha// /}"

  owner="${owner_repo%%/*}"
  repo="${owner_repo##*/}"

  project="${owner}-${repo}"
  url="https://github.com/${owner}/${repo}.git"
  notes=""

  if [ -z "$owner" ] || [ -z "$repo" ] || [ -z "$sha" ]; then
    notes="bad_input_row"
    {
      safe_csv "$project"; echo -n ","
      safe_csv "$owner"; echo -n ","
      safe_csv "$repo"; echo -n ","
      safe_csv "$sha"; echo -n ","
      safe_csv "$url"; echo -n ","
      echo ",,,,,"
      safe_csv "$notes"
      echo
    } >> "$OUT_CSV"
    continue
  fi

  repo_work="${WORKDIR}/${project}_${sha}"
  rm -rf "$repo_work" || true
  mkdir -p "$repo_work"

  # Clone + checkout sha
  if ! timeout -k 9 "$TIMEOUT_CLONE_SEC" git clone --no-checkout "$url" "$repo_work" >/dev/null 2>&1; then
    notes="clone_failed"
    {
      safe_csv "$project"; echo -n ","
      safe_csv "$owner"; echo -n ","
      safe_csv "$repo"; echo -n ","
      safe_csv "$sha"; echo -n ","
      safe_csv "$url"; echo -n ","
      echo ",,,,,"
      safe_csv "$notes"
      echo
    } >> "$OUT_CSV"
    rm -rf "$repo_work" || true
    continue
  fi

  if ! (cd "$repo_work" && git checkout -q "$sha" 2>/dev/null); then
    notes="checkout_failed"
    {
      safe_csv "$project"; echo -n ","
      safe_csv "$owner"; echo -n ","
      safe_csv "$repo"; echo -n ","
      safe_csv "$sha"; echo -n ","
      safe_csv "$url"; echo -n ","
      echo ",,,,,"
      safe_csv "$notes"
      echo
    } >> "$OUT_CSV"
    rm -rf "$repo_work" || true
    continue
  fi

  # GitHub metadata
  repo_json="$(fetch_repo_json "$owner" "$repo")"
  stars="$(json_get "$repo_json" '.stargazers_count // empty')"
  created_at="$(json_get "$repo_json" '.created_at // empty')"
  age_years="$(age_years_from_created_at "$created_at")"

  # SLOC
  sloc="$(compute_sloc "$repo_work")"

  # Commit count (full history best-effort)
  (cd "$repo_work" && git fetch -q --tags --prune --depth=2147483647 2>/dev/null) || true
  commit_count="$(compute_commit_count "$repo_work")"

  # Coverage (best-effort)
  stmt_cov=""
  branch_cov=""
  cov_out="$(compute_coverage "$repo_work" "$TIMEOUT_TESTS_SEC" "$owner" "$repo" "$sha" || true)"
  if [ -n "$cov_out" ]; then
    stmt_cov="$(echo "$cov_out" | awk '{print $1}')"
    branch_cov="$(echo "$cov_out" | awk '{print $2}')"
  fi

  {
    safe_csv "$project"; echo -n ","
    safe_csv "$owner"; echo -n ","
    safe_csv "$repo"; echo -n ","
    safe_csv "$sha"; echo -n ","
    safe_csv "$url"; echo -n ","
    safe_csv "$sloc"; echo -n ","
    safe_csv "$stars"; echo -n ","
    safe_csv "$age_years"; echo -n ","
    safe_csv "$commit_count"; echo -n ","
    safe_csv "$stmt_cov"; echo -n ","
    safe_csv "$branch_cov"; echo -n ","
    safe_csv "$notes"
    echo
  } >> "$OUT_CSV"

  rm -rf "$repo_work" || true
done

echo "Done. Wrote: $OUT_CSV"