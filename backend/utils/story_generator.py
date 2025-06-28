import os
import logging
import google.generativeai as genai
import time

# Configure logging
logger = logging.getLogger(__name__)

def generate_story_with_gemini(prompt, genre, tone, length_in_words):
    """
    Generate a story using the Gemini API with comprehensive error handling.
    """
    try:
        # Validate inputs
        if not prompt or not prompt.strip():
            logger.error("Empty or invalid prompt provided")
            return None
            
        # Configure Gemini with API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return None
            
        logger.info(f"Configuring Gemini API with key: {api_key[:10]}...{api_key[-4:]}")
        genai.configure(api_key=api_key)
        
        # Try different models in order of preference
        models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        
        for model_name in models_to_try:
            logger.info(f"Attempting story generation with {model_name}")
            
            try:
                model = genai.GenerativeModel(model_name)
                
                # Create a more specific prompt
                full_prompt = f"""You are a creative storyteller. Write a complete, engaging story with the following specifications:

Genre: {genre}
Tone: {tone}
Target length: approximately {length_in_words} words
Story premise: {prompt}

Requirements:
- Write a complete story with beginning, middle, and end
- Stay true to the {genre} genre and {tone} tone
- Make it engaging and well-structured
- Write ONLY the story content, no meta-commentary

Story:"""

                logger.info(f"Sending request to {model_name}...")
                logger.debug(f"Full prompt: {full_prompt}")

                # Configure generation parameters based on length
                max_tokens = min(int(length_in_words * 6), 8192)
                
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.8,
                        top_p=0.9,
                        top_k=40
                    )
                )
                
                # Check if response has content
                if hasattr(response, 'text') and response.text:
                    story = response.text.strip()
                    word_count = len(story.split())
                    logger.info(f"✅ Story generated successfully with {model_name}")
                    logger.info(f"Generated {word_count} words (target: {length_in_words})")
                    return story
                elif hasattr(response, 'candidates') and response.candidates:
                    # Check if content was filtered
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        logger.error(f"Content generation stopped: {candidate.finish_reason}")
                        if candidate.finish_reason == "SAFETY":
                            logger.error("Content was filtered for safety reasons. Try a different prompt.")
                        continue
                else:
                    logger.warning(f"Empty response from {model_name}, trying next model...")
                    continue
                    
            except Exception as model_error:
                logger.error(f"Error with {model_name}: {str(model_error)}")
                if "quota" in str(model_error).lower():
                    logger.error("API quota exceeded. Please check your billing and usage limits.")
                    return None
                continue
        
        logger.error("All models failed to generate story")
        return None

    except Exception as e:
        logger.error(f"Critical error in story generation: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def test_story_generation():
    """Simple test function for story generation"""
    logger.info("Running simple story generation test...")
    
    test_story = generate_story_with_gemini(
        prompt="A cat finds a magical door",
        genre="fantasy",
        tone="whimsical",
        length_in_words=100
    )
    
    if test_story:
        logger.info("✅ Test story generation successful")
        logger.info(f"Test story: {test_story[:100]}...")
        return True
    else:
        logger.error("❌ Test story generation failed")
        return False

# Alias for backward compatibility
def generate_story_with_openai(prompt, genre, tone, length):
    """Alias for backward compatibility"""
    return generate_story_with_gemini(prompt, genre, tone, length)

# Fallback function
def generate_story_with_huggingface(prompt, genre, tone, length):
    """Fallback function - not implemented"""
    logger.warning("Hugging Face fallback not implemented")
    return None

if __name__ == "__main__":
    # Run test when script is executed directly
    logging.basicConfig(level=logging.INFO)
    test_story_generation()
