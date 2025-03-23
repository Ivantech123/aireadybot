import os
import logging
import openai
from config.config import OPENAI_API_KEY, OPENAI_ASSISTANT_ID

class OpenAIService:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.assistant_id = OPENAI_ASSISTANT_ID
        openai.api_key = self.api_key
        self.logger = logging.getLogger(__name__)
    
    async def generate_text_response(self, prompt):
        """Generate a text response using ChatGPT"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides informative and concise responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content, response.usage.total_tokens
        except Exception as e:
            self.logger.error(f"Error generating text response: {e}")
            return "Sorry, I encountered an error while processing your request. Please try again later.", 0
    
    async def generate_image(self, prompt):
        """Generate an image using DALL-E"""
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response['data'][0]['url']
        except Exception as e:
            self.logger.error(f"Error generating image: {e}")
            return None
    
    async def transcribe_audio(self, audio_file_path):
        """Transcribe audio to text using Whisper API"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    "whisper-1", 
                    audio_file
                )
            return transcript.text
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return None
