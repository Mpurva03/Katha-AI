from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import logging
import json
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
import google.generativeai as genai
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Import utility modules
from utils.text_analysis import analyze_text
from utils.story_generator import generate_story_with_gemini
from utils.image_generator import create_image_prompt, generate_image, test_image_generation
from utils.audio_generator import generate_speech, test_audio_generation

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Create directories for storing generated content
os.makedirs("temp/images", exist_ok=True)
os.makedirs("temp/audio", exist_ok=True)
os.makedirs("temp/stories", exist_ok=True)

@app.route('/api/generate-story', methods=['POST'])
def generate_story():
    """
    Generate a story based on the provided parameters.
    """
    logger.info("📚 Story generation request received")
    
    try:
        # Check if API keys are available
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        
        if not gemini_key:
            logger.error("❌ GEMINI_API_KEY not configured in environment variables")
            return jsonify({
                "error": "GEMINI_API_KEY not configured. Please check your .env file.",
                "troubleshooting": [
                    "Create a .env file in the project root",
                    "Add: GEMINI_API_KEY=your_actual_api_key",
                    "Get your API key from https://makersuite.google.com/app/apikey"
                ]
            }), 500
            
        # Get request data
        data = request.json
        logger.debug(f"📥 Received request data: {data}")
        
        if not data:
            logger.warning("❌ No data provided in request")
            return jsonify({"error": "No data provided in request body"}), 400
        
        # Extract and validate parameters
        prompt = data.get('prompt', '').strip()
        genre = data.get('genre', 'fantasy')
        tone = data.get('tone', 'adventurous')
        length = data.get('length', 500)
        generate_image_flag = data.get('generateImage', False)
        generate_audio_flag = data.get('generateAudio', False)
        
        logger.info(f"📝 Request parameters:")
        logger.info(f"   Prompt: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")
        logger.info(f"   Genre: {genre}")
        logger.info(f"   Tone: {tone}")
        logger.info(f"   Length: {length}")
        logger.info(f"   Generate Image: {generate_image_flag}")
        logger.info(f"   Generate Audio: {generate_audio_flag}")
        
        # Validate required parameters
        if not prompt:
            logger.warning("❌ Missing required parameter: prompt")
            return jsonify({"error": "Prompt is required and cannot be empty"}), 400
        
        if len(prompt) < 5:
            logger.warning("❌ Prompt too short")
            return jsonify({"error": "Prompt must be at least 5 characters long"}), 400
        
        # Generate story with Gemini
        logger.info("🎭 Starting story generation...")
        try:
            story = generate_story_with_gemini(prompt, genre, tone, length)
            logger.debug(f"📖 Story generation result: {story[:100] if story else 'None'}...")
        except Exception as story_error:
            logger.error(f"❌ Story generation exception: {str(story_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": f"Story generation failed: {str(story_error)}",
                "troubleshooting": [
                    "Check your Gemini API key permissions",
                    "Verify you haven't exceeded API quota",
                    "Try a simpler prompt",
                    "Check the application logs for details"
                ]
            }), 500
        
        if story is None:
            logger.error("❌ Story generation failed - returned None")
            return jsonify({
                "error": "Failed to generate story. The AI service returned no content.",
                "troubleshooting": [
                    "Try a different prompt",
                    "Make sure your prompt doesn't violate content policies",
                    "Check if you've exceeded API quota",
                    "Try reducing the story length",
                    "Ensure your API key has proper permissions"
                ]
            }), 500
        
        if len(story.strip()) < 10:
            logger.error(f"❌ Story too short: {len(story)} characters")
            return jsonify({
                "error": "Generated story is too short. Please try a different prompt.",
                "story_preview": story
            }), 500
        
        logger.info(f"✅ Story generated successfully! Length: {len(story)} characters, {len(story.split())} words")
        
        # Save story to file
        story_id = str(uuid.uuid4())
        story_path = f"temp/stories/{story_id}.txt"
        try:
            with open(story_path, "w", encoding="utf-8") as f:
                f.write(story)
            logger.info(f"💾 Story saved to {story_path}")
        except Exception as save_error:
            logger.error(f"❌ Error saving story: {str(save_error)}")
        
        # Analyze the story
        try:
            logger.info("🔍 Analyzing story...")
            analysis = analyze_text(story)
            logger.info("✅ Story analysis completed")
            logger.debug(f"📊 Analysis result: {analysis}")
        except Exception as analysis_error:
            logger.error(f"❌ Error analyzing text: {str(analysis_error)}")
            analysis = {
                "overall_sentiment": {"compound": 0.0},
                "key_sentences": [],
                "sentence_count": len([s for s in story.split('.') if s.strip()])
            }
        
        # Prepare result
        result = {
            "story": story,
            "storyId": story_id,
            "metadata": {
                "genre": genre,
                "tone": tone,
                "length": length,
                "wordCount": len(story.split()),
                "characterCount": len(story),
                "sentenceCount": analysis["sentence_count"],
                "sentiment": analysis["overall_sentiment"]["compound"]
            }
        }
        
        # Handle image generation request
        if generate_image_flag:
            logger.info("🖼️ Image generation requested with real image APIs...")
            try:
                # Create image prompt
                logger.info("🎨 Creating image prompt...")
                image_prompt = create_image_prompt(story, genre, tone)
                result["imagePrompt"] = image_prompt
                logger.debug(f"🖼️ Image prompt: {image_prompt}")
                
                # Generate real image (no SVG)
                logger.info("🤗 Generating real image...")
                image_path, used_service = generate_image(image_prompt, "huggingface")
                logger.debug(f"🖼️ Image generation result: path={image_path}, service={used_service}")
                
                if image_path:
                    result["imagePath"] = image_path
                    result["imageService"] = used_service
                    result["imageUrl"] = f"/api/image/{os.path.basename(image_path)}"
                    
                    if used_service == "huggingface":
                        logger.info(f"✅ Real image generated successfully with Hugging Face: {image_path}")
                    elif used_service == "stability-ai":
                        logger.info(f"✅ Real image generated successfully with Stability AI: {image_path}")
                    elif used_service == "replicate":
                        logger.info(f"✅ Real image generated successfully with Replicate: {image_path}")
                else:
                    result["imageError"] = "Failed to generate image. All image generation services are currently unavailable. Please check your API keys and try again."
                    logger.error("❌ All real image generation services failed")
                    
            except Exception as img_error:
                logger.error(f"❌ Error in image generation: {str(img_error)}")
                logger.error(f"Image generation traceback: {traceback.format_exc()}")
                result["imageError"] = f"Image generation error: {str(img_error)}"
        
        # Handle audio generation request
        if generate_audio_flag:
            logger.info("🔊 Audio generation requested...")
            try:
                if not openai_key:
                    result["audioError"] = "OpenAI API key not configured. Audio generation requires OPENAI_API_KEY."
                    logger.error("❌ OpenAI API key not found for audio generation")
                else:
                    logger.info("🎤 Generating audio with OpenAI TTS...")
                    audio_path = generate_speech(story)
                    if audio_path:
                        result["audioPath"] = audio_path
                        result["audioUrl"] = f"/api/audio/{os.path.basename(audio_path)}"
                        result["audioService"] = "OpenAI TTS"
                        logger.info(f"✅ Audio generated with OpenAI: {audio_path}")
                    else:
                        result["audioError"] = "Failed to generate audio with OpenAI TTS."
                        logger.error("❌ OpenAI audio generation failed")
            except Exception as audio_err:
                logger.error(f"❌ Audio generation error: {str(audio_err)}")
                result["audioError"] = str(audio_err)

        
        logger.info("✅ Story generation request completed successfully")
        logger.debug(f"📤 Final result keys: {list(result.keys())}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Critical error in story generation: {str(e)}")
        logger.error(f"Critical error traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}",
            "troubleshooting": [
                "Check the application logs for detailed error information",
                "Verify your API keys are correct",
                "Ensure you have sufficient API quota",
                "Try restarting the application",
                "Contact support if the issue persists"
            ]
        }), 500

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio_endpoint():
    """
    Generate audio for existing story text
    """
    logger.info("🔊 Audio generation request received")
    
    try:
        # Check if OpenAI API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            logger.error("❌ OPENAI_API_KEY not configured")
            return jsonify({
                "error": "OpenAI API key not configured. Audio generation requires OPENAI_API_KEY.",
                "troubleshooting": [
                    "Add OPENAI_API_KEY to your .env file",
                    "Get your API key from https://platform.openai.com/api-keys"
                ]
            }), 500
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided in request body"}), 400
        
        text = data.get('text', '').strip()
        story_id = data.get('storyId', str(uuid.uuid4()))
        
        if not text:
            return jsonify({"error": "Text is required for audio generation"}), 400
        
        logger.info(f"🎤 Generating audio for story: {story_id}")
        
        # Generate audio
        audio_path = generate_speech(text)
        
        if audio_path:
            return jsonify({
                "success": True,
                "audioPath": audio_path,
                "audioUrl": f"/api/audio/{os.path.basename(audio_path)}",
                "audioService": "OpenAI TTS"
            })
        else:
            return jsonify({
                "error": "Failed to generate audio with OpenAI TTS"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Audio generation error: {str(e)}")
        return jsonify({
            "error": f"Audio generation failed: {str(e)}"
        }), 500

@app.route('/api/image/<filename>')
def serve_image(filename):
    """Serve generated images (PNG, JPG, SVG)"""
    try:
        image_path = os.path.join("temp/images", filename)
        logger.debug(f"🖼️ Serving image: {image_path}")
        
        if os.path.exists(image_path):
            # Determine MIME type based on file extension
            if filename.endswith('.svg'):
                return send_file(image_path, mimetype='image/svg+xml')
            elif filename.endswith('.png'):
                return send_file(image_path, mimetype='image/png')
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return send_file(image_path, mimetype='image/jpeg')
            else:
                return send_file(image_path, mimetype='image/png')  # Default to PNG
        else:
            logger.error(f"❌ Image not found: {image_path}")
            return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        return jsonify({"error": "Error serving image"}), 500

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        audio_path = os.path.join("temp/audio", filename)
        logger.debug(f"🔊 Serving audio: {audio_path}")
        
        if os.path.exists(audio_path):
            # Determine MIME type based on file extension
            if filename.endswith('.mp3'):
                return send_file(audio_path, mimetype='audio/mpeg')
            elif filename.endswith('.wav'):
                return send_file(audio_path, mimetype='audio/wav')
            else:
                return send_file(audio_path, mimetype='audio/mpeg')  # Default to MP3
        else:
            logger.error(f"❌ Audio not found: {audio_path}")
            return jsonify({"error": "Audio not found"}), 404
    except Exception as e:
        logger.error(f"Error serving audio: {str(e)}")
        return jsonify({"error": "Error serving audio"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    logger.info("🏥 Health check requested")
    
    gemini_key_configured = bool(os.getenv("GEMINI_API_KEY"))
    openai_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    hf_token_configured = bool(os.getenv("HUGGINGFACE_API_TOKEN"))
    stability_key_configured = bool(os.getenv("STABILITY_API_KEY"))
    replicate_token_configured = bool(os.getenv("REPLICATE_API_TOKEN"))
    
    # Test Gemini connection
    gemini_working = False
    gemini_error = None
    if gemini_key_configured:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Hello")
            gemini_working = bool(response.text)
            logger.info("✅ Gemini health check passed")
        except Exception as e:
            gemini_error = str(e)
            logger.error(f"❌ Gemini health check failed: {gemini_error}")
    
    # Test OpenAI connection with actual TTS test
    openai_working = False
    openai_error = None
    if openai_key_configured:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Test actual TTS functionality
            test_response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input="Test"
            )
            
            if test_response.content:
                openai_working = True
                logger.info("✅ OpenAI TTS health check passed")
            else:
                openai_error = "TTS response was empty"
                logger.error("❌ OpenAI TTS returned empty response")
                
        except Exception as e:
            openai_error = str(e)
            logger.error(f"❌ OpenAI TTS health check failed: {openai_error}")
    
    # Test Hugging Face connection
    hf_working = False
    hf_error = None
    if hf_token_configured:
        try:
            import requests
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}"}
            response = requests.get("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0", headers=headers, timeout=10)
            if response.status_code == 200:
                hf_working = True
                logger.info("✅ Hugging Face API health check passed")
            else:
                hf_error = f"HTTP {response.status_code}"
                logger.error(f"❌ Hugging Face API returned: {response.status_code}")
        except Exception as e:
            hf_error = str(e)
            logger.error(f"❌ Hugging Face health check failed: {hf_error}")
    
    # Check capabilities
    image_generation_available = hf_token_configured and hf_working
    audio_generation_available = openai_key_configured and openai_working

    # Determine primary image generation method
    if hf_token_configured and hf_working:
        image_method = "Hugging Face Stable Diffusion"
    elif stability_key_configured:
        image_method = "Stability AI"
    elif replicate_token_configured:
        image_method = "Replicate"
    else:
        image_method = "Not Available"
    
    health_status = {
        "status": "healthy" if (gemini_key_configured and gemini_working) else "unhealthy",
        "gemini_api_configured": gemini_key_configured,
        "gemini_working": gemini_working,
        "gemini_error": gemini_error,
        "openai_api_configured": openai_key_configured,
        "openai_working": openai_working,
        "openai_error": openai_error,
        "huggingface_api_configured": hf_token_configured,
        "huggingface_working": hf_working,
        "huggingface_error": hf_error,
        "stability_api_configured": stability_key_configured,
        "image_generation_available": image_generation_available or gemini_key_configured,
        "image_generation_method": image_method,
        "audio_generation_available": audio_generation_available,
        "audio_generation_method": "OpenAI TTS" if audio_generation_available else "Not Available",
        "services": {
            "story_generation": "Gemini API",
            "text_analysis": "Gemini API", 
            "image_generation": image_method,
            "audio_generation": "OpenAI TTS" if audio_generation_available else "Not Available"
        },
        "version": "4.0.0",
        "features": [
            "Story generation with Gemini",
            "Text analysis with Gemini", 
            "High-quality image generation with Hugging Face" if hf_working else "SVG image generation with Gemini",
            "Audio generation with OpenAI TTS" if audio_generation_available else "Audio generation disabled",
            "Multiple image generation fallbacks"
        ],
        "debug_info": {
            "python_version": os.sys.version,
            "gemini_version": genai.__version__ if 'genai' in globals() else "Not available",
            "api_keys_configured": {
                "gemini": gemini_key_configured,
                "openai": openai_key_configured,
                "huggingface": hf_token_configured,
                "stability": stability_key_configured,
                "replicate": replicate_token_configured
            },
            "directories_exist": {
                "temp/images": os.path.exists("temp/images"),
                "temp/audio": os.path.exists("temp/audio"),
                "temp/stories": os.path.exists("temp/stories")
            }
        }
    }
    
    return jsonify(health_status)

@app.route('/api/test-image', methods=['POST'])
def test_image_generation_endpoint():
    """Test image generation with Hugging Face"""
    try:
        data = request.json or {}
        prompt = data.get('prompt', 'A beautiful magical forest with glowing trees and mystical creatures')
        
        logger.info(f"🧪 Testing Hugging Face image generation")
        
        image_path, used_service = generate_image(f"{prompt} Genre: fantasy Tone: whimsical", "huggingface")
        
        if image_path:
            return jsonify({
                "success": True,
                "imagePath": image_path,
                "imageService": used_service,
                "imageUrl": f"/api/image/{os.path.basename(image_path)}",
                "message": f"Image generated successfully with {used_service}!"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate image with any available service"
            }), 500
            
    except Exception as e:
        logger.error(f"Test image generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/test-audio', methods=['POST'])
def test_audio_generation_endpoint():
    """Test OpenAI TTS audio generation"""
    try:
        data = request.json or {}
        text = data.get('text', 'Hello, this is a test of OpenAI text-to-speech functionality.')
        
        logger.info(f"🧪 Testing OpenAI TTS generation")
        
        # Check if OpenAI API key is configured
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({
                "success": False,
                "error": "OpenAI API key not configured",
                "troubleshooting": [
                    "Add OPENAI_API_KEY to your .env file",
                    "Get your API key from https://platform.openai.com/api-keys",
                    "Make sure your OpenAI account has sufficient credits"
                ]
            }), 500
        
        audio_path = generate_speech(text)
        
        if audio_path:
            return jsonify({
                "success": True,
                "audioPath": audio_path,
                "audioUrl": f"/api/audio/{os.path.basename(audio_path)}",
                "message": "Audio generated successfully with OpenAI TTS!",
                "audioService": "OpenAI TTS"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate audio with OpenAI TTS",
                "troubleshooting": [
                    "Check your OpenAI API key",
                    "Verify your OpenAI account has sufficient credits",
                    "Check the application logs for detailed errors"
                ]
            }), 500
            
    except Exception as e:
        logger.error(f"Test audio generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "troubleshooting": [
                "Check your OpenAI API key configuration",
                "Verify your OpenAI account status",
                "Check the application logs for detailed errors"
            ]
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5500))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info("🚀 Starting AI Story Generator API")
    logger.info(f"📍 Port: {port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info("🤖 Using Gemini API for story generation and text analysis")
    logger.info("🎤 Using OpenAI API for audio generation")
    logger.info("🖼️ Using Hugging Face for high-quality image generation")
    
    # Check API configurations
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    stability_key = os.getenv("STABILITY_API_KEY")
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    
    if gemini_key:
        logger.info(f"✅ Gemini API key configured: {gemini_key[:10]}...{gemini_key[-4:]}")
        logger.info("📚 Story generation available with Gemini")
        logger.info("🔍 Text analysis available with Gemini")
    else:
        logger.error("❌ GEMINI_API_KEY not found!")
    
    if openai_key:
        logger.info(f"✅ OpenAI API key configured: {openai_key[:10]}...{openai_key[-4:]}")
        logger.info("🔊 Audio generation available with OpenAI TTS")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found - audio generation will not be available")
    
    if hf_token:
        logger.info(f"✅ Hugging Face API token configured: {hf_token[:10]}...{hf_token[-4:]}")
        logger.info("🖼️ High-quality image generation available with Hugging Face")
    else:
        logger.warning("⚠️ HUGGINGFACE_API_TOKEN not found - will use SVG fallback")
    
    if stability_key:
        logger.info(f"✅ Stability AI API key configured: {stability_key[:10]}...{stability_key[-4:]}")
        logger.info("🎨 Stability AI available as backup image generation")
    else:
        logger.info("ℹ️ STABILITY_API_KEY not found - Stability AI not available")
    
    if replicate_token:
        logger.info(f"✅ Replicate API token configured: {replicate_token[:10]}...{replicate_token[-4:]}")
        logger.info("🖼️ Replicate available as backup image generation")
    else:
        logger.info("ℹ️ REPLICATE_API_TOKEN not found - Replicate AI not available")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
