# Educational Video Generator

This script generates an educational video about a given topic using AI for content, TTS for audio, and Manim for animations.

## Usage

Run the script from the parent directory:

```bash
cd edu_video_generator
python -m src.main "Your Topic" [--language <lang_code>] [--voice <voice_name>]
```

-   `"Your Topic"`: The subject for the video (e.g., "Photosynthesis").
-   `--language <lang_code>`: Optional. Specify the language (e.g., `en-US`, `hi-IN`). Defaults to `en-US`.
-   `--voice <voice_name>`: Optional. Specify a specific TTS voice (e.g., `af_bella`, `hf_beta`). If omitted, uses the default voice for the selected language.

## Examples

```bash
# Generate video on Photosynthesis in English (default voice af_heart)
python -m src.main "Photosynthesis" --language en-US

# Generate video on Indian History in Hindi (default voice hf_alpha)
python -m src.main "भारत का इतिहास" --language hi-IN

# Generate video on Photosynthesis using a specific English voice
python -m src.main "Photosynthesis" --language en-US --voice af_bella
```

## Available Languages and Voices

The following language codes (`--language`) and voice names (`--voice`) are supported by the TTS API:

*   **en-US** (American English - Default Voice: `af_heart`)
    *   `af_heart`, `af_alloy`, `af_aoede`, `af_bella`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky`, `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa`
*   **en-GB** (British English - Default Voice: `bf_alice`)
    *   `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`, `bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis`
*   **es-ES** (Spanish - Default Voice: `ef_dora`)
    *   `ef_dora`, `em_alex`, `em_santa`
*   **fr-FR** (French - Default Voice: `ff_siwis`)
    *   `ff_siwis`
*   **hi-IN** (Hindi - Default Voice: `hf_alpha`)
    *   `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`
*   **it-IT** (Italian - Default Voice: `if_sara`)
    *   `if_sara`, `im_nicola`
*   **ja-JP** (Japanese - Default Voice: `jf_alpha`)
    *   `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`, `jm_kumo`
*   **pt-BR** (Brazilian Portuguese - Default Voice: `pf_dora`)
    *   `pf_dora`, `pm_alex`, `pm_santa`
*   **zh-CN** (Mandarin Chinese - Default Voice: `zf_xiaobei`)
    *   `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`, `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang`
