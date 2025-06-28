import os
import uuid
import logging
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

def generate_speech(text, voice_preset="alloy", output_path=None):
    """
    Generate speech using OpenAI's text-to-speech API
    """
    if output_path is None:
        output_path = f"temp/audio/speech_{uuid.uuid4()}.mp3"
    
    try:
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return None
            
        client = OpenAI(api_key=api_key)
        
        # Limit text length for API constraints (4096 characters max)
        if len(text) > 4000:
            text = text[:4000] + "..."
            logger.info(f"Text truncated to 4000 characters for TTS")
        
        # Available voices: alloy, echo, fable, onyx, nova, shimmer
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice_preset not in valid_voices:
            voice_preset = "alloy"
        
        logger.info(f"Generating speech with OpenAI TTS using voice: {voice_preset}")
        
        # Generate speech using OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice=voice_preset,
            input=text,
            response_format="mp3"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the audio file
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Speech generated and saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating speech with OpenAI: {str(e)}")
        
        # Fallback to gTTS if OpenAI fails
        try:
            logger.info("Falling back to gTTS...")
            from gtts import gTTS
            
            # Limit text length for gTTS
            if len(text) > 5000:
                text = text[:5000] + "..."
            
            # Generate speech with gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Change extension to wav for gTTS
            fallback_path = output_path.replace('.mp3', '.wav')
            tts.save(fallback_path)
            
            logger.info(f"Fallback speech generated with gTTS: {fallback_path}")
            return fallback_path
            
        except Exception as fallback_error:
            logger.error(f"Fallback gTTS also failed: {str(fallback_error)}")
            return None

def test_audio_generation():
    """Test OpenAI TTS generation"""
    logger.info("Testing OpenAI TTS generation...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("✅ OpenAI API key configured - TTS generation available")
        
        # Test with a short text
        test_text = "Hello, this is a test of OpenAI's text-to-speech functionality."
        result = generate_speech(test_text)
        
        if result:
            logger.info("✅ OpenAI TTS test successful")
            return True
        else:
            logger.error("❌ OpenAI TTS test failed")
            return False
    else:
        logger.warning("❌ OpenAI API key not found - TTS generation not available")
        return False

if __name__ == "__main__":
    # Test audio generation when script is executed directly
    logging.basicConfig(level=logging.INFO)
    test_audio_generation()
