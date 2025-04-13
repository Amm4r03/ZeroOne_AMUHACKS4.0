import base64
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from enum import Enum
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Voice Data ---
# Extracted VoiceURI values from voicedata.txt
VALID_VOICES = [
    "af-ZA-AdriNeural", "af-ZA-WillemNeural", "sq-AL-AnilaNeural", "sq-AL-IlirNeural",
    "am-ET-AmehaNeural", "am-ET-MekdesNeural", "ar-DZ-AminaNeural", "ar-DZ-IsmaelNeural",
    "ar-BH-AliNeural", "ar-BH-LailaNeural", "ar-EG-SalmaNeural", "ar-EG-ShakirNeural",
    "ar-IQ-BasselNeural", "ar-IQ-RanaNeural", "ar-JO-SanaNeural", "ar-JO-TaimNeural",
    "ar-KW-FahedNeural", "ar-KW-NouraNeural", "ar-LB-LaylaNeural", "ar-LB-RamiNeural",
    "ar-LY-ImanNeural", "ar-LY-OmarNeural", "ar-MA-JamalNeural", "ar-MA-MounaNeural",
    "ar-OM-AbdullahNeural", "ar-OM-AyshaNeural", "ar-QA-AmalNeural", "ar-QA-MoazNeural",
    "ar-SA-HamedNeural", "ar-SA-ZariyahNeural", "ar-SY-AmanyNeural", "ar-SY-LaithNeural",
    "ar-TN-HediNeural", "ar-TN-ReemNeural", "ar-AE-FatimaNeural", "ar-AE-HamdanNeural",
    "ar-YE-MaryamNeural", "ar-YE-SalehNeural", "az-AZ-BabekNeural", "az-AZ-BanuNeural",
    "bn-BD-NabanitaNeural", "bn-BD-PradeepNeural", "bn-IN-BashkarNeural", "bn-IN-TanishaaNeural",
    "bs-BA-GoranNeural", "bs-BA-VesnaNeural", "bg-BG-BorislavNeural", "bg-BG-KalinaNeural",
    "my-MM-NilarNeural", "my-MM-ThihaNeural", "ca-ES-EnricNeural", "ca-ES-JoanaNeural",
    "zh-HK-HiuGaaiNeural", "zh-HK-HiuMaanNeural", "zh-HK-WanLungNeural", "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural", "zh-CN-YunjianNeural", "zh-CN-YunxiNeural", "zh-CN-YunxiaNeural",
    "zh-CN-YunyangNeural", "zh-CN-liaoning-XiaobeiNeural", "zh-TW-HsiaoChenNeural",
    "zh-TW-YunJheNeural", "zh-TW-HsiaoYuNeural", "zh-CN-shaanxi-XiaoniNeural",
    "hr-HR-GabrijelaNeural", "hr-HR-SreckoNeural", "cs-CZ-AntoninNeural", "cs-CZ-VlastaNeural",
    "da-DK-ChristelNeural", "da-DK-JeppeNeural", "nl-BE-ArnaudNeural", "nl-BE-DenaNeural",
    "nl-NL-ColetteNeural", "nl-NL-FennaNeural", "nl-NL-MaartenNeural", "en-AU-NatashaNeural",
    "en-AU-WilliamNeural", "en-CA-ClaraNeural", "en-CA-LiamNeural", "en-HK-SamNeural",
    "en-HK-YanNeural", "en-IN-NeerjaExpressiveNeural", "en-IN-NeerjaNeural", "en-IN-PrabhatNeural",
    "en-IE-ConnorNeural", "en-IE-EmilyNeural", "en-KE-AsiliaNeural", "en-KE-ChilembaNeural",
    "en-NZ-MitchellNeural", "en-NZ-MollyNeural", "en-NG-AbeoNeural", "en-NG-EzinneNeural",
    "en-PH-JamesNeural", "en-PH-RosaNeural", "en-SG-LunaNeural", "en-SG-WayneNeural",
    "en-ZA-LeahNeural", "en-ZA-LukeNeural", "en-TZ-ElimuNeural", "en-TZ-ImaniNeural",
    "en-GB-LibbyNeural", "en-GB-MaisieNeural", "en-GB-RyanNeural", "en-GB-SoniaNeural",
    "en-GB-ThomasNeural", "en-US-AvaMultilingualNeural", "en-US-AndrewMultilingualNeural",
    "en-US-EmmaMultilingualNeural", "en-US-BrianMultilingualNeural", "en-US-AvaNeural",
    "en-US-AndrewNeural", "en-US-EmmaNeural", "en-US-BrianNeural", "en-US-AnaNeural",
    "en-US-AriaNeural", "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-GuyNeural",
    "en-US-JennyNeural", "en-US-MichelleNeural", "en-US-RogerNeural", "en-US-SteffanNeural",
    "et-EE-AnuNeural", "et-EE-KertNeural", "fil-PH-AngeloNeural", "fil-PH-BlessicaNeural",
    "fi-FI-HarriNeural", "fi-FI-NooraNeural", "fr-BE-CharlineNeural", "fr-BE-GerardNeural",
    "fr-CA-ThierryNeural", "fr-CA-AntoineNeural", "fr-CA-JeanNeural", "fr-CA-SylvieNeural",
    "fr-FR-VivienneMultilingualNeural", "fr-FR-RemyMultilingualNeural", "fr-FR-DeniseNeural",
    "fr-FR-EloiseNeural", "fr-FR-HenriNeural", "fr-CH-ArianeNeural", "fr-CH-FabriceNeural",
    "gl-ES-RoiNeural", "gl-ES-SabelaNeural", "ka-GE-EkaNeural", "ka-GE-GiorgiNeural",
    "de-AT-IngridNeural", "de-AT-JonasNeural", "de-DE-SeraphinaMultilingualNeural",
    "de-DE-FlorianMultilingualNeural", "de-DE-AmalaNeural", "de-DE-ConradNeural",
    "de-DE-KatjaNeural", "de-DE-KillianNeural", "de-CH-JanNeural", "de-CH-LeniNeural",
    "el-GR-AthinaNeural", "el-GR-NestorasNeural", "gu-IN-DhwaniNeural", "gu-IN-NiranjanNeural",
    "he-IL-AvriNeural", "he-IL-HilaNeural", "hi-IN-MadhurNeural", "hi-IN-SwaraNeural",
    "hu-HU-NoemiNeural", "hu-HU-TamasNeural", "is-IS-GudrunNeural", "is-IS-GunnarNeural",
    "id-ID-ArdiNeural", "id-ID-GadisNeural", "ga-IE-ColmNeural", "ga-IE-OrlaNeural",
    "it-IT-GiuseppeNeural", "it-IT-DiegoNeural", "it-IT-ElsaNeural", "it-IT-IsabellaNeural",
    "ja-JP-KeitaNeural", "ja-JP-NanamiNeural", "jv-ID-DimasNeural", "jv-ID-SitiNeural",
    "kn-IN-GaganNeural", "kn-IN-SapnaNeural", "kk-KZ-AigulNeural", "kk-KZ-DauletNeural",
    "km-KH-PisethNeural", "km-KH-SreymomNeural", "ko-KR-HyunsuNeural", "ko-KR-InJoonNeural",
    "ko-KR-SunHiNeural", "lo-LA-ChanthavongNeural", "lo-LA-KeomanyNeural", "lv-LV-EveritaNeural",
    "lv-LV-NilsNeural", "lt-LT-LeonasNeural", "lt-LT-OnaNeural", "mk-MK-AleksandarNeural",
    "mk-MK-MarijaNeural", "ms-MY-OsmanNeural", "ms-MY-YasminNeural", "ml-IN-MidhunNeural",
    "ml-IN-SobhanaNeural", "mt-MT-GraceNeural", "mt-MT-JosephNeural", "mr-IN-AarohiNeural",
    "mr-IN-ManoharNeural", "mn-MN-BataaNeural", "mn-MN-YesuiNeural", "ne-NP-HemkalaNeural",
    "ne-NP-SagarNeural", "nb-NO-FinnNeural", "nb-NO-PernilleNeural", "ps-AF-GulNawazNeural",
    "ps-AF-LatifaNeural", "fa-IR-DilaraNeural", "fa-IR-FaridNeural", "pl-PL-MarekNeural",
    "pl-PL-ZofiaNeural", "pt-BR-ThalitaNeural", "pt-BR-AntonioNeural", "pt-BR-FranciscaNeural",
    "pt-PT-DuarteNeural", "pt-PT-RaquelNeural", "ro-RO-AlinaNeural", "ro-RO-EmilNeural",
    "ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural", "sr-RS-NicholasNeural", "sr-RS-SophieNeural",
    "si-LK-SameeraNeural", "si-LK-ThiliniNeural", "sk-SK-LukasNeural", "sk-SK-ViktoriaNeural",
    "sl-SI-PetraNeural", "sl-SI-RokNeural", "so-SO-MuuseNeural", "so-SO-UbaxNeural",
    "es-AR-ElenaNeural", "es-AR-TomasNeural", "es-BO-MarceloNeural", "es-BO-SofiaNeural",
    "es-CL-CatalinaNeural", "es-CL-LorenzoNeural", "es-ES-XimenaNeural", "es-ES-AlvaroNeural",
    "es-ES-ElviraNeural", "es-CO-GonzaloNeural", "es-CO-SalomeNeural", "es-CR-JuanNeural",
    "es-CR-MariaNeural", "es-CU-BelkysNeural", "es-CU-ManuelNeural", "es-DO-EmilioNeural",
    "es-DO-RamonaNeural", "es-EC-AndreaNeural", "es-EC-LuisNeural", "es-SV-LorenaNeural",
    "es-SV-RodrigoNeural", "es-GQ-JavierNeural", "es-GQ-TeresaNeural", "es-GT-AndresNeural",
    "es-GT-MartaNeural", "es-HN-CarlosNeural", "es-HN-KarlaNeural", "es-MX-DaliaNeural",
    "es-MX-JorgeNeural", "es-NI-FedericoNeural", "es-NI-YolandaNeural", "es-PA-MargaritaNeural",
    "es-PA-RobertoNeural", "es-PY-MarioNeural", "es-PY-TaniaNeural", "es-PE-AlexNeural",
    "es-PE-CamilaNeural", "es-PR-KarinaNeural", "es-PR-VictorNeural", "es-US-AlonsoNeural",
    "es-US-PalomaNeural", "es-UY-MateoNeural", "es-UY-ValentinaNeural", "es-VE-PaolaNeural",
    "es-VE-SebastianNeural", "su-ID-JajangNeural", "su-ID-TutiNeural", "sw-KE-RafikiNeural",
    "sw-KE-ZuriNeural", "sw-TZ-DaudiNeural", "sw-TZ-RehemaNeural", "sv-SE-MattiasNeural",
    "sv-SE-SofieNeural", "ta-IN-PallaviNeural", "ta-IN-ValluvarNeural", "ta-MY-KaniNeural",
    "ta-MY-SuryaNeural", "ta-SG-AnbuNeural", "ta-SG-VenbaNeural", "ta-LK-KumarNeural",
    "ta-LK-SaranyaNeural", "te-IN-MohanNeural", "te-IN-ShrutiNeural", "th-TH-NiwatNeural",
    "th-TH-PremwadeeNeural", "tr-TR-AhmetNeural", "tr-TR-EmelNeural", "uk-UA-OstapNeural",
    "uk-UA-PolinaNeural", "ur-IN-GulNeural", "ur-IN-SalmanNeural", "ur-PK-AsadNeural",
    "ur-PK-UzmaNeural", "uz-UZ-MadinaNeural", "uz-UZ-SardorNeural", "vi-VN-HoaiMyNeural",
    "vi-VN-NamMinhNeural", "cy-GB-AledNeural", "cy-GB-NiaNeural", "zu-ZA-ThandoNeural",
    "zu-ZA-ThembaNeural"
]

# Create an Enum for voices
VoiceEnum = Enum("VoiceEnum", {voice: voice for voice in VALID_VOICES})

# --- Pydantic Request Model ---
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize")
    voice: VoiceEnum = Field(..., description="Voice model to use")
    rate: float = Field(default=1.0, ge=0.1, le=2.0, description="Speech rate (0.1 to 2.0)")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Speech volume (0.0 to 1.0)")
    with_speechmarks: bool = Field(default=True, description="Include speechmarks data")

# --- Headers for CloudTTS API ---
CLOUDTTS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Host': 'cloudtts.com',
    'Origin': 'https://cloudtts.com',
    'Referer': 'https://cloudtts.com/u/index.html',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Brave";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1'
}

CLOUDTTS_URL = 'https://cloudtts.com/api/get_audio'

# --- FastAPI App ---
app = FastAPI(title="CloudTTS Proxy API")

@app.get("/", summary="Root endpoint to check server status")
async def read_root():
    """Returns a simple message indicating the server is running."""
    return {"message": "CloudTTS Proxy API is running"}

@app.post("/tts",
          summary="Synthesize speech using CloudTTS",
          response_description="The synthesized audio file (MP3 format)")
async def synthesize_speech(request: TTSRequest):
    """
    Takes text and configuration, calls the CloudTTS API, and returns the audio.
    """
    payload = {
        "rate": request.rate,
        "volume": request.volume,
        "recording": False,
        "text": request.text,
        "voice": request.voice.value, # Get the string value from Enum
        "with_speechmarks": request.with_speechmarks
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Increased timeout
            logger.info(f"Sending request to CloudTTS: {payload}")
            response = await client.post(
                CLOUDTTS_URL,
                headers=CLOUDTTS_HEADERS,
                json=payload
            )
            response.raise_for_status() # Raise exception for 4xx/5xx errors

            response_data = response.json()
            logger.info(f"Received response status: {response.status_code}")
            # Log the raw response data for debugging
            # logger.debug(f"Raw CloudTTS response data: {response_data}") # Be careful logging potentially large data

            if response_data.get("success") and "data" in response_data and "audio" in response_data["data"]:
                base64_audio = response_data["data"]["audio"]
                logger.info(f"Extracted Base64 audio string (length: {len(base64_audio)})")
                # logger.debug(f"Base64 string (first 100 chars): {base64_audio[:100]}") # Log beginning of string

                if not base64_audio:
                    logger.error("Received empty audio string from CloudTTS.")
                    raise HTTPException(status_code=502, detail="CloudTTS returned empty audio data.")

                try:
                    audio_bytes = base64.b64decode(base64_audio)
                    logger.info(f"Decoded audio bytes length: {len(audio_bytes)}")
                    if not audio_bytes:
                         logger.error("Decoded audio bytes are empty.")
                         raise HTTPException(status_code=500, detail="Failed to decode audio data correctly (empty result).")
                    return Response(content=audio_bytes, media_type="audio/mpeg")
                except Exception as e:
                    logger.error(f"Error decoding Base64 audio: {e}")
                    raise HTTPException(status_code=500, detail="Failed to decode audio data from CloudTTS")
            else:
                error_msg = response_data.get("msg", "Unknown error from CloudTTS")
                logger.error(f"CloudTTS API returned an error: {error_msg}")
                # Pass through the error message if available
                raise HTTPException(status_code=502, detail=f"CloudTTS API Error: {error_msg}")

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        detail = f"CloudTTS API request failed with status {status_code}"
        try:
            # Try to get more details from the response body if it's JSON
            error_details = e.response.json()
            detail += f": {error_details.get('msg', e.response.text)}"
        except Exception:
            # Fallback if response is not JSON or parsing fails
             detail += f": {e.response.text}"

        logger.error(detail)
        # Map specific errors if needed, e.g., 429 to 429
        if status_code == 429:
             raise HTTPException(status_code=429, detail="Rate limit exceeded with CloudTTS API")
        else:
             raise HTTPException(status_code=502, detail=detail) # 502 Bad Gateway for upstream errors

    except httpx.RequestError as e:
        logger.error(f"Error connecting to CloudTTS API: {e}")
        raise HTTPException(status_code=504, detail=f"Could not connect to CloudTTS API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# --- Run Server ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000)) # Allow configuring port via environment variable
    uvicorn.run(app, host="0.0.0.0", port=port)
