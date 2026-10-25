#!/bin/sh
# Wan 2.2 Enhanced NSFW (image to video) — everything the worker image needs. The Dockerfile in your copy downloads this file
# from the original repo on every build, so fixes made there reach you with a rebuild.
set -eu
case "${CIVITAI_TOKEN:-}" in ""|PASTE_*) echo "ERROR: set CIVITAI_TOKEN at the top of the Dockerfile" >&2; exit 1;; esac

# file <dest> <url> <sha256>
file() {
  wget -q -O "$1" "$2"
  echo "$3  $1" | sha256sum -c - || { echo "ERROR: $1 changed upstream — wait for an update of the original repo, then rebuild" >&2; exit 1; }
}

# Civitai 2053259 / version 2477539 (13.3 GB)
file /comfyui/models/diffusion_models/wan22_enhanced_nsfw_fastmove_v2_fp8_high.safetensors \
  "https://civitai.com/api/download/models/2477539?fileId=2366050&token=${CIVITAI_TOKEN}" \
  65d97ca22ed892321c0e24e89ac4779937dac6505a1d641a27fee8057b7fb4e8

# Civitai 2053259 / version 2477548 (13.3 GB)
file /comfyui/models/diffusion_models/wan22_enhanced_nsfw_fastmove_v2_fp8_low.safetensors \
  "https://civitai.com/api/download/models/2477548?fileId=2366064&token=${CIVITAI_TOKEN}" \
  2ac7a7df968f40d60c8418f2b6c0dd82677f043409f70a38261be4e924d85939

# Comfy-Org/Wan-2.1 (Apache 2.0) (6.7 GB)
file /comfyui/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors \
  "https://huggingface.co/Comfy-Org/Wan-2.1/resolve/123acf1cc74bccbb9bfff8ac1ee72edc08c2341d/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
  c3355d30191f1f066b26d93fba017ae9809dce6c627dda5f6a66eaa651204f68

# Comfy-Org/Wan-2.1 (0.3 GB)
file /comfyui/models/vae/wan_2.1_vae.safetensors \
  "https://huggingface.co/Comfy-Org/Wan-2.1/resolve/123acf1cc74bccbb9bfff8ac1ee72edc08c2341d/split_files/vae/wan_2.1_vae.safetensors" \
  2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b

# ComfyUI 0.34.0 (base image) → 0.39.0 — for the newest Wan nodes. Install into /opt/venv (the one ComfyUI actually runs with).
cd /comfyui
git fetch --depth 1 https://github.com/Comfy-Org/ComfyUI.git tag v0.39.0
git checkout -f v0.39.0
uv pip install --python /opt/venv/bin/python -r requirements.txt "transformers>=4.50.3,<5" "huggingface-hub<1.0"
timeout 300 /opt/venv/bin/python main.py --quick-test-for-ci --cpu
