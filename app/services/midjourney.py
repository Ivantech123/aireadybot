import aiohttp
import asyncio
import logging
import json
import base64

class MidJourneyError(Exception):
    def __init__(self, msg: str = "Error"):
        self.msg = msg
    
    def output(self):
        logging.error("MidJourney error:", self.msg)

class MidJourney:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.novita.ai/v2/imagine"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_image(self, prompt: str):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "prompt": prompt,
                    "model": "midjourney-v6",  # u0418u0441u043fu043eu043bu044cu0437u0443u0435u043c MidJourney v6
                    "num_images": 1,
                    "width": 1024,
                    "height": 1024,
                    "steps": 50,
                    "guidance_scale": 7.5
                }
                
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # u041fu0440u043eu0432u0435u0440u044fu0435u043c u0444u043eu0440u043cu0430u0442 u043eu0442u0432u0435u0442u0430 u0432 u0437u0430u0432u0438u0441u0438u043cu043eu0441u0442u0438 u043eu0442 API
                        if "images" in result and result["images"]:
                            return result["images"][0]  # u0412u043eu0437u0432u0440u0430u0449u0430u0435u043c URL u0438u043bu0438 base64 u0434u0430u043du043du044bu0435 u043au0430u0440u0442u0438u043du043au0438
                        elif "task_id" in result:
                            # u0415u0441u043bu0438 API u0440u0430u0431u043eu0442u0430u0435u0442 u0430u0441u0438u043du0445u0440u043eu043du043du043e, u043fu043eu043bu0443u0447u0430u0435u043c u0440u0435u0437u0443u043bu044cu0442u0430u0442 u043fu043e task_id
                            return await self._poll_task_result(session, result["task_id"])
                        else:
                            raise MidJourneyError(f"Unexpected response format: {result}")
                    else:
                        error_text = await response.text()
                        raise MidJourneyError(f"API request failed with status {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            err = MidJourneyError(str(e))
            err.output()
            raise err
        except Exception as e:
            err = MidJourneyError(str(e))
            err.output()
            raise err
    
    async def _poll_task_result(self, session, task_id, max_attempts=30, delay=2):
        """u041eu043fu0440u0430u0448u0438u0432u0430u0435u043c API u0434u043bu044f u043fu043eu043bu0443u0447u0435u043du0438u044f u0440u0435u0437u0443u043bu044cu0442u0430u0442u0430 u043fu043e task_id"""
        check_url = f"https://api.novita.ai/v2/task/{task_id}"
        
        for attempt in range(max_attempts):
            async with session.get(check_url, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # u041fu0440u043eu0432u0435u0440u044fu0435u043c u0441u0442u0430u0442u0443u0441 u0437u0430u0434u0430u0447u0438
                    if result.get("status") == "completed":
                        if "images" in result and result["images"]:
                            return result["images"][0]
                        else:
                            raise MidJourneyError(f"Task completed but no images found: {result}")
                    elif result.get("status") == "failed":
                        raise MidJourneyError(f"Task failed: {result.get('error', 'Unknown error')}")
                    
                    # u0417u0430u0434u0430u0447u0430 u0435u0449u0435 u0432u044bu043fu043eu043bu043du044fu0435u0442u0441u044f, u0436u0434u0435u043c
                    await asyncio.sleep(delay)
                else:
                    error_text = await response.text()
                    raise MidJourneyError(f"Failed to check task status: {response.status} - {error_text}")
        
        raise MidJourneyError(f"Timeout waiting for task {task_id} to complete after {max_attempts} attempts")
    
    async def decode_image(self, base64_string):
        """u0414u0435u043au043eu0434u0438u0440u0443u0435u0442 base64 u0432 u0431u0438u043du0430u0440u043du044bu0435 u0434u0430u043du043du044bu0435"""
        try:
            if base64_string.startswith("data:image"):
                # u0415u0441u043bu0438 u044du0442u043e data URL, u0438u0437u0432u043bu0435u043au0430u0435u043c u0442u043eu043bu044cu043au043e base64 u0447u0430u0441u0442u044c
                base64_string = base64_string.split(",")[1]
            
            image_data = base64.b64decode(base64_string)
            return image_data
        except Exception as e:
            err = MidJourneyError(f"Failed to decode base64 image: {str(e)}")
            err.output()
            raise err
