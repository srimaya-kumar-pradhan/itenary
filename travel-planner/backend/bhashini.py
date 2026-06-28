"""
Bhashini ULCA API Translation Service.
Proxies translation requests through the backend to keep API credentials secure.

Flow:
1. Client sends text + target language to /api/translate
2. Backend calls Bhashini getModelsPipeline to discover inference endpoints
3. Backend calls the inference endpoint for batch translation
4. Returns translated text to client

Supports all 22 scheduled languages of India via Bhashini NMT models.
"""

import logging
from typing import List, Optional, Dict, Any
import requests
from config import settings

logger = logging.getLogger(__name__)

# Bhashini language code mapping (ISO 639-1 → Bhashini internal codes)
BHASHINI_LANG_MAP = {
    "hi": "hi",   # Hindi
    "ta": "ta",   # Tamil
    "te": "te",   # Telugu
    "bn": "bn",   # Bengali
    "mr": "mr",   # Marathi
    "gu": "gu",   # Gujarati
    "kn": "kn",   # Kannada
    "ml": "ml",   # Malayalam
    "pa": "pa",   # Punjabi
    "or": "or",   # Odia
    "as": "as",   # Assamese
    "ur": "ur",   # Urdu
    "ne": "ne",   # Nepali
    "sd": "sd",   # Sindhi
    "sa": "sa",   # Sanskrit
    "en": "en",   # English
}

ULCA_BASE_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
PIPELINE_ID = "64392f96daac500b55c543cd"


class BhashiniService:
    """Bhashini ULCA translation service with pipeline caching."""

    def __init__(self):
        self.user_id: str = getattr(settings, "bhashini_user_id", "")
        self.api_key: str = getattr(settings, "bhashini_api_key", "")
        self.available: bool = bool(self.user_id and self.api_key)
        self._pipeline_cache: Dict[str, Dict[str, Any]] = {}

        if self.available:
            logger.info("Bhashini translation service initialized")
        else:
            logger.info("Bhashini credentials not set — translation proxy disabled")

    def _get_pipeline(self, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Discover the Bhashini inference endpoint for a language pair.
        Caches results to avoid repeated pipeline discovery calls.
        """
        cache_key = f"{source_lang}_{target_lang}"
        if cache_key in self._pipeline_cache:
            return self._pipeline_cache[cache_key]

        src = BHASHINI_LANG_MAP.get(source_lang, source_lang)
        tgt = BHASHINI_LANG_MAP.get(target_lang, target_lang)

        try:
            resp = requests.post(
                ULCA_BASE_URL,
                json={
                    "pipelineTasks": [{
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": src,
                                "targetLanguage": tgt,
                            }
                        }
                    }],
                    "pipelineRequestConfig": {
                        "pipelineId": PIPELINE_ID,
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "userID": self.user_id,
                    "ulcaApiKey": self.api_key,
                },
                timeout=10,
            )

            if resp.status_code != 200:
                logger.warning(f"Bhashini pipeline discovery failed: {resp.status_code}")
                return None

            data = resp.json()

            # Extract inference endpoint and service ID
            pipeline_config = data.get("pipelineResponseConfig", [{}])
            inference_endpoint = None
            if pipeline_config:
                cfg = pipeline_config[0] if isinstance(pipeline_config, list) else pipeline_config
                inference_endpoint = cfg.get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl")

            tasks = data.get("pipelineResponseConfig", [{}])
            service_id = None
            response_config = data.get("pipelineResponseConfig", [])

            # Try to get from response
            if isinstance(response_config, list) and len(response_config) > 0:
                task_configs = response_config[0].get("pipelineInferenceAPIEndPoint", {})
                inference_endpoint = task_configs.get("callbackUrl", inference_endpoint)

            # Get serviceId from pipelineResponseConfig
            infer_config = data.get("pipelineInferenceAPIEndPoint", {})
            if infer_config:
                inference_endpoint = inference_endpoint or infer_config.get("callbackUrl")

            lang_resp = data.get("languages", [])
            if lang_resp and isinstance(lang_resp, list):
                for lr in lang_resp:
                    if lr.get("sourceLanguage") == src and lr.get("targetLanguage") == tgt:
                        service_id = lr.get("serviceId")
                        break

            # Alternative extraction path
            pipeline_tasks = data.get("pipelineResponseConfig", [])
            if isinstance(pipeline_tasks, list):
                for pt in pipeline_tasks:
                    endpoint_info = pt.get("pipelineInferenceAPIEndPoint", {})
                    inference_endpoint = inference_endpoint or endpoint_info.get("callbackUrl")
                    schema = endpoint_info.get("inferenceApiKey", {})

            if not inference_endpoint:
                logger.warning("No inference endpoint found in Bhashini response")
                return None

            result = {
                "inference_url": inference_endpoint,
                "service_id": service_id,
                "source": src,
                "target": tgt,
                "api_key": data.get("pipelineInferenceAPIEndPoint", {}).get("inferenceApiKey", {}).get("value", self.api_key),
            }

            self._pipeline_cache[cache_key] = result
            logger.info(f"Bhashini pipeline cached for {src}→{tgt}")
            return result

        except Exception as e:
            logger.error(f"Bhashini pipeline discovery error: {e}")
            return None

    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """
        Translate a batch of texts using the Bhashini NMT inference endpoint.
        Returns original texts on failure.
        """
        if not self.available:
            return texts

        if target_lang not in BHASHINI_LANG_MAP:
            logger.info(f"Language '{target_lang}' not supported by Bhashini")
            return texts

        pipeline = self._get_pipeline(source_lang, target_lang)
        if not pipeline:
            return texts

        try:
            # Build input array
            input_data = [{"source": text} for text in texts]

            body = {
                "pipelineTasks": [{
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": pipeline["source"],
                            "targetLanguage": pipeline["target"],
                        },
                    }
                }],
                "inputData": {
                    "input": input_data,
                }
            }

            if pipeline.get("service_id"):
                body["pipelineTasks"][0]["config"]["serviceId"] = pipeline["service_id"]

            headers = {
                "Content-Type": "application/json",
                "Authorization": pipeline.get("api_key", self.api_key),
            }

            resp = requests.post(
                pipeline["inference_url"],
                json=body,
                headers=headers,
                timeout=30,
            )

            if resp.status_code != 200:
                logger.warning(f"Bhashini translation failed: {resp.status_code}")
                return texts

            data = resp.json()

            # Extract translations from response
            output = data.get("pipelineResponse", [{}])
            if isinstance(output, list) and len(output) > 0:
                translated_output = output[0].get("output", [])
                if translated_output:
                    return [item.get("target", texts[i]) for i, item in enumerate(translated_output)]

            return texts

        except Exception as e:
            logger.error(f"Bhashini translation error: {e}")
            return texts

    def transliterate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Transliterate text (phonetic conversion) for nouns, addresses, locations.
        Falls back to original text on failure.
        """
        if not self.available:
            return text

        try:
            # Use the transliteration pipeline
            resp = requests.post(
                ULCA_BASE_URL,
                json={
                    "pipelineTasks": [{
                        "taskType": "transliteration",
                        "config": {
                            "language": {
                                "sourceLanguage": BHASHINI_LANG_MAP.get(source_lang, source_lang),
                                "targetLanguage": BHASHINI_LANG_MAP.get(target_lang, target_lang),
                            }
                        }
                    }],
                    "pipelineRequestConfig": {
                        "pipelineId": PIPELINE_ID,
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "userID": self.user_id,
                    "ulcaApiKey": self.api_key,
                },
                timeout=10,
            )

            if resp.status_code != 200:
                return text

            data = resp.json()
            endpoint_info = data.get("pipelineResponseConfig", [{}])
            if isinstance(endpoint_info, list) and len(endpoint_info) > 0:
                inference_url = endpoint_info[0].get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl")
            else:
                return text

            if not inference_url:
                return text

            # Call inference
            trans_resp = requests.post(
                inference_url,
                json={
                    "pipelineTasks": [{
                        "taskType": "transliteration",
                        "config": {
                            "language": {
                                "sourceLanguage": BHASHINI_LANG_MAP.get(source_lang, source_lang),
                                "targetLanguage": BHASHINI_LANG_MAP.get(target_lang, target_lang),
                            }
                        }
                    }],
                    "inputData": {
                        "input": [{"source": text}],
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": data.get("pipelineInferenceAPIEndPoint", {}).get("inferenceApiKey", {}).get("value", self.api_key),
                },
                timeout=10,
            )

            if trans_resp.status_code == 200:
                output = trans_resp.json().get("pipelineResponse", [{}])
                if isinstance(output, list) and len(output) > 0:
                    results = output[0].get("output", [{}])
                    if results:
                        return results[0].get("target", text)

            return text

        except Exception as e:
            logger.error(f"Bhashini transliteration error: {e}")
            return text


# Singleton instance
bhashini_service = BhashiniService()
