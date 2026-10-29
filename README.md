# Wan 2.2 Enhanced NSFW (image to video) — RunPod Serverless worker

> 🔞 **Adult (18+) · NSFW** — part of afterdark-workers, workers for uncensored adult image and video models.

A ready-to-build [RunPod Serverless](https://runpod.io?ref=qpguwapm) worker for **[Wan 2.2 Enhanced NSFW FastMove v2](https://civitai.com/models/2053259?modelVersionId=2477539)** by [taek75799](https://civitai.com/user/taek75799), an adult Wan 2.2 14B image-to-video fine-tune (4 steps). Based on the official [`runpod/worker-comfyui`](https://github.com/runpod-workers/worker-comfyui).

Models are baked into the image, so a cold start does not re-download anything.

> 18+ model. You download it with your own Civitai account and are responsible for following the model licenses.

## What's inside

| File | Source | Size |
|---|---|---|
| `diffusion_models/wan22_enhanced_nsfw_fastmove_v2_fp8_high.safetensors` | [Civitai 2053259 / version 2477539](https://civitai.com/models/2053259?modelVersionId=2477539) | 13.3 GB |
| `diffusion_models/wan22_enhanced_nsfw_fastmove_v2_fp8_low.safetensors` | [Civitai 2053259 / version 2477548](https://civitai.com/models/2053259?modelVersionId=2477548) | 13.3 GB |
| `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` | [Comfy-Org/Wan-2.1](https://huggingface.co/Comfy-Org/Wan-2.1) (Apache 2.0) | 6.7 GB |
| `vae/wan_2.1_vae.safetensors` | [Comfy-Org/Wan-2.1](https://huggingface.co/Comfy-Org/Wan-2.1) | 0.3 GB |

Just the model as its creator released it — no LoRAs, no extra nodes. All files are checked by SHA-256 at build time. ComfyUI is upgraded to 0.39.0.

## Setup (about 10 minutes + build time)

New to this? Follow the [step-by-step setup guide](https://cobaltpear.github.io/guide.html).

1. **Make your own private copy** — click **Use this template** → **Create a new repository** → choose **Private**.
   (Your Civitai token will be in it, so it must stay private.)
2. **Add your Civitai token** — get one at civitai.com → Account settings → **Security & Apps** → **API Keys** → **Add API key** → Permission preset **Read Only**.
   In your copy, open `Dockerfile` → ✏️ edit → replace `PASTE_YOUR_CIVITAI_TOKEN_HERE` on line 6 → Commit.
   No RunPod account yet? [Sign up here](https://runpod.io?ref=qpguwapm) — a referral link: after you first add $10, RunPod gives you a bonus credit (usually $5–10) and this repo a small credit.
3. **Create the endpoint** — see [Create the endpoint](#create-the-endpoint) below.
4. **Create an API key** — RunPod → Settings → API Keys → **Restricted**, allow only this endpoint.

## Create the endpoint

RunPod → **Serverless** → **New Endpoint** → **Deploy from a GitHub repository** → pick your copy (the first time, **Edit connection** lets RunPod see it). Then, top to bottom on the page:

| Where on the page | What to set |
|---|---|
| **Endpoint name** | anything — your copy's name is fine |
| **GPU configuration** | tick a box of 48 GB or more (more boxes = easier to get a GPU) |
| **Max workers** | `1` |
| Click **Advanced settings** to open it: | |
| → **Active workers** | `0` — nothing to pay while idle |
| → **GPU count** | `1` |
| → **Idle timeout** | `5` sec |
| → **Enable FlashBoot** | on (the switch) · **Standard** |
| → **Enable execution timeout** | on · **Execution timeout** `900` sec |
| → click **Container configuration** to open it → **Container disk** | 60 GB |

Leave everything else as it is, then **Deploy** at the bottom. The first build takes about 45 minutes. The very first request after that waits another 10–15 minutes while a worker pulls the image; later cold starts are much faster.

## Or run it on Modal

The same worker also runs on [Modal](https://modal.com) — another serverless GPU service, billed by the second — from `modal_app.py` in this repo. It builds the same `Dockerfile` and answers the same requests as on RunPod (`/run`, `/status/<id>`), so a client that calls RunPod endpoints needs only the other address and key.

On your computer, with Python 3.10 or newer, in a copy of your repo (`git clone` it, with your `Dockerfile` lines filled in):

```sh
pip install modal
modal setup                                                   # opens a page to sign in to Modal
modal secret create cobaltpear-key CP_KEY=<a long password you make up>
modal deploy modal_app.py                                     # builds, then prints the worker's address
```

- The address ending in `-api….modal.run` is your endpoint; send `Authorization: Bearer <that password>` with each request.
- GPU: the `GPU` line at the top of `modal_app.py` (48 GB by default). A worker turns off 60 s after its last picture.
- Modal needs a payment method on your account to use GPUs. Its prices: [modal.com/pricing](https://modal.com/pricing).
- Updates: run `modal deploy modal_app.py` again.

## Updates

Your copy only holds the token. The build steps (`build.sh`, `handler.py`) are downloaded from this repo on every build, so when something changes upstream (a model file is replaced, ComfyUI needs an update) it is fixed here — you just rebuild your endpoint.

To rebuild: commit any change to the `main` branch of your copy — RunPod builds again on every push to `main` (the endpoint's **Builds** tab shows it). Nothing to change? Edit `README.md` (✏️), add a line, **Commit changes…** → **Commit changes**.

### Model version

This repo always follows the version the model's creator currently recommends. Now: **FastMove v2, Civitai versions 2477539 (high) + 2477548 (low)**.
Each change of the build files is kept as a release (`files-…`). To stay on one, replace `latest/download` with `download/files-…` (that release's name) in both `ADD` lines of your `Dockerfile`.

## Use it

Any client that sends ComfyUI API-format workflows to RunPod works. `pack.json` in this repo holds the workflow and tells a client where the prompt, seed and size go (format `pack/1`, engine `comfyui`).

Raw request:

```bash
IMG=$(base64 -w0 photo.png)
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync \
  -H "Authorization: Bearer <API_KEY>" -H "Content-Type: application/json" \
  -d "{\"input\": {\"workflow\": $(jq .workflow pack.json | jq '.["6"].inputs.text = "she turns her head and smiles" | .["30"].inputs.noise_seed = 1'), \"images\": [{\"name\": \"start_image.png\", \"image\": \"$IMG\"}]}}"
```

Your picture goes in `images` under the name `start_image.png` — the workflow's LoadImage node reads it from there.

The video (WEBM) comes back as base64 in `output.images[0].data`.

Tips: Starts from your picture: 81 frames (5 s at 16 fps), 4 steps. Describe the motion, not the picture.

### LoRAs

- **Per picture:** send up to 4 LoRAs with a request: `input.remote_loras` = `[{"name": "remote_<id>.safetensors", "url": "<download link>", "sha256": "<file sha256>"}]` plus a `LoraLoader` reading that name in the workflow — the worker downloads each once and keeps it while it runs. [Cobalt Pear](https://cobaltpear.github.io/) does all of this from a Civitai or Hugging Face link. For more than 4, set the environment variable `REMOTE_LORA_MAX` (e.g. `8`) on your endpoint (**Manage → Edit Endpoint → Environment Variables**).
- **Built in:** put links in the `LORAS` line of your `Dockerfile` — each followed by its strength — and rebuild. They are downloaded once at build time, so a fresh worker doesn't download them again. A request picks which ones it uses with `input.baked_loras` = `[{"link": "<link from LORAS>", "strength": 0.8}]` (`[]` = none); without it every one is used at its `LORAS` strength. One that isn't built in (yet) is left out and named in `output.warning`, and `output.built_in` lists the built-in LoRAs. Put their trigger words in your prompt yourself. To accept only built-in LoRAs, set `REMOTE_LORA_MAX` to `0`.
- Pick LoRAs made for this model's base model — the worker warns (`output.warning`) when one doesn't fit.

### Compatible clients

- [Cobalt Pear](https://cobaltpear.github.io/) — a one-page web app: add this repo's URL, your endpoint ID and API key, then just type a prompt. Everything stays in your browser. [Try the demo](https://cobaltpear.github.io/demo/) without RunPod. What's different for these workers there: [Use with Cobalt Pear](https://afterdark-workers.github.io/cobalt-pear/).

Questions or ideas: [Discussions](https://github.com/afterdark-workers/afterdark-workers.github.io/discussions).
