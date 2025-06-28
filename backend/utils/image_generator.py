import os
import logging
import uuid
import requests
import base64
from io import BytesIO
import google.generativeai as genai

# Configure logging
logger = logging.getLogger(__name__)

def generate_image_with_huggingface(prompt, model="stabilityai/stable-diffusion-xl-base-1.0"):
    """
    Generate image using Hugging Face Inference API
    """
    try:
        # Get Hugging Face API token
        hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not hf_token:
            logger.error("HUGGINGFACE_API_TOKEN not found in environment variables")
            return None, "no_token"
        
        # Hugging Face Inference API endpoint
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare the payload
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
                "width": 768,
                "height": 768
            }
        }
        
        logger.info(f"Generating image with Hugging Face ({model}): {prompt[:50]}...")
        
        # Make the API request
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            # Check if response is actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type and len(response.content) < 1000:
                # Might be an error message
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        logger.error(f"Hugging Face API error: {error_data['error']}")
                        if 'loading' in error_data['error'].lower():
                            return None, "loading"
                        return None, "api_error"
                except:
                    pass
            
            # Save the image
            image_id = str(uuid.uuid4())
            image_filename = f"story_image_{image_id}.png"
            image_path = f"temp/images/{image_filename}"
            
            # Ensure directory exists
            os.makedirs("temp/images", exist_ok=True)
            
            with open(image_path, "wb") as f:
                f.write(response.content)
            
            # Verify the file was created and has content
            if os.path.exists(image_path) and os.path.getsize(image_path) > 1000:
                logger.info(f"✅ Image generated successfully with Hugging Face: {image_path}")
                return image_path, "huggingface"
            else:
                logger.error("Generated file is too small or doesn't exist")
                return None, "invalid_file"
            
        elif response.status_code == 503:
            logger.warning("⏳ Hugging Face model is loading, this may take a few minutes")
            return None, "loading"
        elif response.status_code == 429:
            logger.warning("⚠️ Rate limited by Hugging Face API")
            return None, "rate_limited"
        else:
            logger.error(f"❌ Hugging Face API error: {response.status_code} - {response.text}")
            return None, "api_error"
            
    except requests.exceptions.Timeout:
        logger.error("❌ Hugging Face API request timed out")
        return None, "timeout"
    except Exception as e:
        logger.error(f"Error generating image with Hugging Face: {str(e)}")
        return None, "error"

def generate_image_with_stability_ai(prompt):
    """
    Generate image using Stability AI API
    """
    try:
        # Get Stability AI API key
        stability_key = os.getenv("STABILITY_API_KEY")
        if not stability_key:
            logger.error("STABILITY_API_KEY not found in environment variables")
            return None, "no_token"
        
        api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 768,
            "width": 768,
            "samples": 1,
            "steps": 30,
        }
        
        logger.info(f"Generating image with Stability AI: {prompt[:50]}...")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            if "artifacts" not in data or len(data["artifacts"]) == 0:
                logger.error("No artifacts in Stability AI response")
                return None, "no_artifacts"
            
            # Decode the base64 image
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            
            # Save the image
            image_id = str(uuid.uuid4())
            image_filename = f"story_image_{image_id}.png"
            image_path = f"temp/images/{image_filename}"
            
            # Ensure directory exists
            os.makedirs("temp/images", exist_ok=True)
            
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            # Verify the file was created and has content
            if os.path.exists(image_path) and os.path.getsize(image_path) > 1000:
                logger.info(f"✅ Image generated successfully with Stability AI: {image_path}")
                return image_path, "stability-ai"
            else:
                logger.error("Generated file is too small or doesn't exist")
                return None, "invalid_file"
        else:
            logger.error(f"❌ Stability AI API error: {response.status_code} - {response.text}")
            return None, "api_error"
            
    except requests.exceptions.Timeout:
        logger.error("❌ Stability AI API request timed out")
        return None, "timeout"
    except Exception as e:
        logger.error(f"Error generating image with Stability AI: {str(e)}")
        return None, "error"

def generate_image_with_replicate(prompt):
    """
    Generate image using Replicate API (another alternative)
    """
    try:
        # Get Replicate API token
        replicate_token = os.getenv("REPLICATE_API_TOKEN")
        if not replicate_token:
            logger.error("REPLICATE_API_TOKEN not found in environment variables")
            return None, "no_token"
        
        import replicate
        
        logger.info(f"Generating image with Replicate: {prompt[:50]}...")
        
        # Use SDXL model on Replicate
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "width": 768,
                "height": 768,
                "num_inference_steps": 30,
                "guidance_scale": 7.5
            }
        )
        
        if output and len(output) > 0:
            # Download the image
            image_url = output[0]
            response = requests.get(image_url, timeout=60)
            
            if response.status_code == 200:
                # Save the image
                image_id = str(uuid.uuid4())
                image_filename = f"story_image_{image_id}.png"
                image_path = f"temp/images/{image_filename}"
                
                # Ensure directory exists
                os.makedirs("temp/images", exist_ok=True)
                
                with open(image_path, "wb") as f:
                    f.write(response.content)
                
                if os.path.exists(image_path) and os.path.getsize(image_path) > 1000:
                    logger.info(f"✅ Image generated successfully with Replicate: {image_path}")
                    return image_path, "replicate"
                else:
                    logger.error("Generated file is too small or doesn't exist")
                    return None, "invalid_file"
        
        return None, "no_output"
        
    except Exception as e:
        logger.error(f"Error generating image with Replicate: {str(e)}")
        return None, "error"

def create_image_prompt(story, genre, tone):
    """
    Create a detailed prompt for image generation based on the story using Gemini API
    """
    try:
        # Configure Gemini with API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return f"A {tone} {genre} story scene with characters in an interesting setting, high quality digital art"
            
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel("gemini-1.5-flash")

        system_prompt = """You are an expert at creating detailed image prompts for AI image generation.
Create a vivid, detailed description that captures the most visual and compelling scene from the story.
Focus on the setting, characters, mood, lighting, and atmosphere.
Include specific visual details like colors, lighting, composition, and style.
Keep it concise but rich in visual details (max 150 words).
This will be used with Stable Diffusion or similar AI image models.

Important: Create prompts that will generate actual photorealistic or artistic images, not diagrams or text.
Include art style keywords like: digital art, concept art, detailed, high quality, photorealistic, fantasy art, etc.

Format: [Main subject/scene], [setting/background], [lighting/mood], [art style], [additional details]"""

        user_prompt = f"Create a detailed image generation prompt from this story:\n\nStory: {story[:500]}...\n\nGenre: {genre}\nTone: {tone}"

        response = model.generate_content(
            f"{system_prompt}\n\n{user_prompt}",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=200,
                temperature=0.7
            )
        )
        
        if response.text:
            prompt = response.text.strip()
            
            # Enhance the prompt for better image generation
            style_keywords = {
                "fantasy": "fantasy art, magical, ethereal, detailed digital art",
                "sci-fi": "sci-fi art, futuristic, cyberpunk, concept art, detailed",
                "horror": "dark art, gothic, atmospheric, dramatic lighting, detailed",
                "romance": "romantic art, soft lighting, beautiful, detailed digital art",
                "adventure": "adventure art, dynamic, action scene, detailed digital art",
                "mystery": "mysterious art, noir style, dramatic shadows, detailed"
            }
            
            genre_style = style_keywords.get(genre.lower(), "detailed digital art")
            enhanced_prompt = f"{prompt}, {genre_style}, high quality, trending on artstation, masterpiece"
            
            logger.info(f"Generated image prompt: {enhanced_prompt}")
            return enhanced_prompt
        else:
            return f"A {tone} {genre} story scene with characters in an interesting setting, high quality digital art, detailed, masterpiece"
            
    except Exception as e:
        logger.error(f"Error creating image prompt with Gemini API: {str(e)}")
        return f"A {tone} {genre} story scene with characters in an interesting setting, high quality digital art, detailed, masterpiece"

def generate_image(prompt, preferred_service="huggingface"):
    """
    Generate image using the preferred service with fallbacks - NO SVG GENERATION
    """
    logger.info(f"Generating real image with {preferred_service}: {prompt[:50]}...")
    
    # List of Hugging Face models to try in order of preference
    huggingface_models = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "runwayml/stable-diffusion-v1-5", 
        "CompVis/stable-diffusion-v1-4",
        "stabilityai/stable-diffusion-2-1",
        "prompthero/openjourney-v4"
    ]
    
    # Try Hugging Face models
    if preferred_service == "huggingface" or preferred_service == "auto":
        for model in huggingface_models:
            logger.info(f"🤗 Trying Hugging Face model: {model}")
            image_path, status = generate_image_with_huggingface(prompt, model)
            
            if image_path:
                return image_path, "huggingface"
            elif status == "loading":
                logger.info(f"⏳ Model {model} is loading, trying next...")
                continue
            elif status == "rate_limited":
                logger.warning(f"⚠️ Rate limited on {model}, trying next...")
                continue
            else:
                logger.warning(f"❌ Failed with {model}: {status}")
                continue
    
    # Try Stability AI as backup
    logger.info("🎨 Trying Stability AI...")
    stability_result, status = generate_image_with_stability_ai(prompt)
    if stability_result:
        return stability_result, "stability-ai"
    else:
        logger.warning(f"❌ Stability AI failed: {status}")
    
    # Try Replicate as another backup
    logger.info("🔄 Trying Replicate...")
    replicate_result, status = generate_image_with_replicate(prompt)
    if replicate_result:
        return replicate_result, "replicate"
    else:
        logger.warning(f"❌ Replicate failed: {status}")
    
    # No more fallbacks - return None
    logger.error("❌ All image generation services failed - no image will be generated")
    return None, "all_failed"

def test_image_generation():
    """
    Test image generation with available services
    """
    logger.info("Testing real image generation services...")
    
    services_available = 0
    
    # Test Hugging Face
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if hf_token:
        logger.info("✅ Hugging Face API token configured")
        
        # Test with a simple prompt
        test_result, status = generate_image_with_huggingface("A beautiful landscape with mountains and a lake, digital art, high quality")
        if test_result:
            logger.info("✅ Hugging Face image generation test successful")
            services_available += 1
        else:
            logger.warning(f"⚠️ Hugging Face image generation test failed: {status}")
    else:
        logger.warning("❌ Hugging Face API token not found")
    
    # Test Stability AI
    stability_key = os.getenv("STABILITY_API_KEY")
    if stability_key:
        logger.info("✅ Stability AI API key configured")
        services_available += 1
    else:
        logger.warning("❌ Stability AI API key not found")
    
    # Test Replicate
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if replicate_token:
        logger.info("✅ Replicate API token configured")
        services_available += 1
    else:
        logger.warning("❌ Replicate API token not found")
    
    if services_available == 0:
        logger.error("❌ No image generation services available!")
        return False
    else:
        logger.info(f"✅ {services_available} image generation service(s) available")
        return True

# Legacy function names for backward compatibility - all redirect to real image generation
def generate_image_with_dalle(prompt):
    """Legacy function - redirects to Hugging Face"""
    return generate_image(prompt, "huggingface")

def generate_image_with_dalle_2(prompt):
    """Legacy function - redirects to Hugging Face"""
    return generate_image(prompt, "huggingface")

def generate_image_with_huggingface_legacy(prompt):
    """Legacy function - redirects to new Hugging Face function"""
    return generate_image(prompt, "huggingface")

if __name__ == "__main__":
    # Test image generation when script is executed directly
    test_image_generation()
