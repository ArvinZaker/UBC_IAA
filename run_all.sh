#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly VENV_DIR="${PROJECT_ROOT}/.venv"
readonly REQUIRED_PYTHON="3.12"
readonly CACHE_DIR="${PROJECT_ROOT}/.cache"

cd "${PROJECT_ROOT}"
mkdir -p "${CACHE_DIR}/matplotlib" "${CACHE_DIR}/pip"
export MPLCONFIGDIR="${CACHE_DIR}/matplotlib"
export PIP_CACHE_DIR="${CACHE_DIR}/pip"
export XDG_CACHE_HOME="${CACHE_DIR}"

if command -v g++ >/dev/null 2>&1; then
  libstdcpp="$(g++ -print-file-name=libstdc++.so.6)"
  if [[ -f "${libstdcpp}" ]]; then
    export LD_LIBRARY_PATH="$(dirname -- "${libstdcpp}"):${LD_LIBRARY_PATH:-}"
  fi
fi

python_version() {
  "$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null
}

find_python() {
  local candidate
  for candidate in python3.12 python3 python; do
    if command -v "${candidate}" >/dev/null 2>&1 \
      && [[ "$(python_version "${candidate}")" == "${REQUIRED_PYTHON}" ]]; then
      command -v "${candidate}"
      return 0
    fi
  done
  return 1
}

venv_version=""
if [[ -e "${VENV_DIR}" || -L "${VENV_DIR}" ]]; then
  if [[ -x "${VENV_DIR}/bin/python" ]]; then
    venv_version="$(python_version "${VENV_DIR}/bin/python")"
  fi

  if [[ "${venv_version}" != "${REQUIRED_PYTHON}" ]]; then
    backup_path="${PROJECT_ROOT}/.venv.incompatible.$(date +%Y%m%d%H%M%S)"
    echo "Moving incompatible .venv to ${backup_path##*/}"
    mv "${VENV_DIR}" "${backup_path}"
  fi
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  if ! SYSTEM_PYTHON="$(find_python)"; then
    echo "Python ${REQUIRED_PYTHON} is required." >&2
    echo "Install Python ${REQUIRED_PYTHON}, or run this project with: nix develop" >&2
    exit 1
  fi

  echo "Creating .venv with Python ${REQUIRED_PYTHON}"
  "${SYSTEM_PYTHON}" -m venv "${VENV_DIR}"
fi

readonly VENV_PYTHON="${VENV_DIR}/bin/python"

echo "Installing project dependencies into .venv"
"${VENV_PYTHON}" -m pip install --disable-pip-version-check -r requirements.txt

echo
echo "[1/2] Building Anki deck"
"${VENV_PYTHON}" build_anki_deck.py

echo
echo "[2/2] Generating project-status image"
MPLBACKEND=Agg "${VENV_PYTHON}" generate_project_status.py

echo
echo "All builds completed successfully."
