# AI job capacity preflight

This standard-library-only tool checks a **declared capacity envelope** before a
model download or inference job. It does not download models, install software,
start inference, accept licenses, or prove that generated assets work in YUGA.

From the repository root:

```sh
python3 games/yuga-native/tools/ai-assets/preflight.py \
  --required-vram-gib 8 --required-free-disk-gib 20 \
  --reserve-disk-gib 1 --path /workspace \
  --output /absolute/new/preflight.json
python3 -m unittest discover -s games/yuga-native/tools/ai-assets -p 'test_*.py' -v
```

The example is an **illustrative budget**, not a measured model requirement.
Set VRAM to the pinned model's peak requirement **plus operational headroom**.
Set required free disk to all **new weights, environment/dependencies, extracted
files, download caches and scratch output**, then retain a separate reserve.
Estimate both final and temporary storage; a compressed download size is not the
entire requirement. A model's published minimum may leave no room for the editor,
display, other models or inference overhead. Run again immediately before a job;
this tool does not reserve memory or prevent another process from allocating it.

Exit `0` means only declared capacity is available; exit `2` means capacity is
insufficient/unknown or arguments are invalid. The JSON differentiates observed
hardware from requirements and lists unverified aspects. Output receipts refuse
to overwrite existing files. CUDA qualification requires one GPU's **free**
memory to meet the requirement; several cards are never implicitly pooled.
Malformed/failed NVIDIA queries cannot qualify a CUDA job.

Use `--cpu-only` **instead of** `--required-vram-gib` only when the selected model
has independently verified CPU support. CPU mode still checks disk capacity, but
does not establish sufficient RAM, practical speed or supported operators.
Cgroup v2 CPU/memory caps are reported where readable; absent or unlimited caps
are explicit and do not imply unlimited physical memory. CUDA versions, kernels,
Blackwell compatibility, RAM peaks, network access, model permissions and art
quality need separate checks. Do not download weights in a capacity-constrained
workspace merely because a model's source repository is accessible.
