import os
import requests
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

class ElevenLabsVoice:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set")
    
    def get_voices(self) -> List[Dict]:
        # Get all available voices
        url = f"{self.base_url}/voices"
        response = requests.get(url, headers={"xi-api-key": self.api_key})
        
        if response.status_code == 200:
            return response.json().get("voices", [])
        else:
            raise Exception(f"Failed to get voices: {response.text}")
    
    def generate_speech(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM", 
                       model_id: str = "eleven_monolingual_v1",
                       stability: float = 0.5, similarity_boost: float = 0.75) -> Dict:
        # Generate speech from text
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }
        
        response = requests.post(
            url,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code == 200:
            # Save audio to file
            audio_path = f"/tmp/speech_{voice_id}.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            return {
                "success": True,
                "audio_path": audio_path,
                "voice_id": voice_id,
                "text_length": len(text),
                "model_used": model_id
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def clone_voice(self, name: str, description: str, files: List[str]) -> Dict:
        # Clone a voice from audio files
        url = f"{self.base_url}/voices/add"
        
        payload = {
            "name": name,
            "description": description
        }
        
        files_data = []
        for file_path in files:
            with open(file_path, "rb") as f:
                files_data.append(("files", f))
        
        response = requests.post(
            url,
            headers={"xi-api-key": self.api_key},
            data=payload,
            files=files_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}

def generate_voice_from_text(text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> Dict:
    # Generate voice from text
    try:
        elevenlabs = ElevenLabsVoice()
        return elevenlabs.generate_speech(text, voice_id)
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_available_voices() -> List[Dict]:
    # Get available voices
    try:
        elevenlabs = ElevenLabsVoice()
        return elevenlabs.get_voices()
    except Exception as e:
        return [{"error": str(e)}]
