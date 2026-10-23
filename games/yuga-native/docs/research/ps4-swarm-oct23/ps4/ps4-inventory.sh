#!/usr/bin/env bash
# Read-only inventory for an already running PS4 Linux installation.
# No root, installation, firmware changes, model downloads or network requests.
set -u
export LC_ALL=C

probe_gpu=0
case "${1:-}" in
  "") ;;
  --gpu) probe_gpu=1 ;;
  *) printf 'Usage: bash ps4-inventory.sh [--gpu]\n' >&2; exit 2 ;;
esac

run_check() {
  local label=$1
  shift
  printf '\n%s\n' "$label"
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'UNAVAILABLE: %s\n' "$1"
    return 0
  fi
  "$@"
  local status=$?
  printf 'exit_status=%s\n' "$status"
  return 0
}

printf 'PS4 Linux inventory — run on the console, not the laptop/cloud\n'
run_check 'Kernel and architecture' uname -srvmo
if [[ -r /etc/os-release ]]; then
  run_check 'Linux distribution' cat /etc/os-release
fi
run_check 'CPU model, topology and exposed instruction flags' lscpu
run_check 'Memory actually exposed to Linux (kB)' awk \
  '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ {print}' /proc/meminfo
run_check 'Current filesystem capacity' df -hT . /tmp
run_check 'PCI devices and bound kernel drivers' lspci -nnk

printf '\nGPU device nodes and permissions\n'
found_device=0
for device in /dev/dri/card* /dev/dri/renderD* /dev/kfd; do
  [[ -e "$device" ]] || continue
  found_device=1
  ls -l "$device"
done
[[ "$found_device" -eq 1 ]] || printf 'No DRM or KFD device nodes found.\n'

printf '\nRelevant configuration of the running kernel, if published locally\n'
config_filter='^(# )?CONFIG_(X86_PS4|DRM_RADEON|DRM_AMDGPU|DRM_AMDGPU_CIK|HSA_AMD)(=| )'
kernel_config="/boot/config-$(uname -r)"
if [[ -r /proc/config.gz ]] && command -v zgrep >/dev/null 2>&1; then
  zgrep -E "$config_filter" /proc/config.gz || true
elif [[ -r "$kernel_config" ]]; then
  grep -E "$config_filter" "$kernel_config" || true
else
  printf 'Running-kernel config is not readable; do not substitute a downloaded fork config.\n'
fi

run_check 'CMake availability' cmake --version
run_check 'C compiler availability' cc --version
run_check 'C++ compiler availability' c++ --version
run_check 'libc version when reported by getconf' getconf GNU_LIBC_VERSION
run_check 'Python availability for CPU task scripts' python3 --version
run_check 'Node availability for project tooling' node --version
run_check 'Git availability' git --version
run_check 'SSH client availability (server status is separate)' ssh -V
run_check 'Listening TCP sockets for SSH and local inference' ss -ltn \
  '( sport = :22 or sport = :8080 or sport = :8081 )'

if [[ "$probe_gpu" -eq 1 ]]; then
  if command -v timeout >/dev/null 2>&1 && command -v vulkaninfo >/dev/null 2>&1; then
    run_check 'Optional Vulkan summary; software devices are not GPU evidence' \
      timeout 15s vulkaninfo --summary
  else
    printf '\nVulkan probe skipped: timeout and/or vulkaninfo is not installed.\n'
  fi
else
  printf '\nVulkan runtime probe not requested. Use --gpu only if desired.\n'
fi

printf '\nInventory complete. No PS4 inference/build or GPU speed claim follows from this output.\n'
