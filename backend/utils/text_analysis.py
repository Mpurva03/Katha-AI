import os
import logging
import json
import google.generativeai as genai

# Configure logging
logger = logging.getLogger(__name__)

def analyze_text(text):
    """
    Analyze text using the Gemini API to extract overall sentiment,
    key sentences, and sentence count.
    """
    try:
        # Configure Gemini with API key
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Use a Gemini model suitable for text analysis
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Create analysis prompt
        analysis_prompt = f"""Analyze the following text and provide its overall sentiment,
a list of 1 to 3 key sentences that best represent its core message or emotional highlights,
and the total number of sentences in the text.

Return the result in JSON format with the following structure:
{{
  "overall_sentiment": {{"compound": 0.5}},
  "key_sentences": ["sentence1", "sentence2"],
  "sentence_count": 5
}}

The compound score should be between -1 (very negative) and 1 (very positive).

Text to analyze:
---
{text}
---
"""

        logger.info("Sending text analysis request to Gemini API...")

        response = model.generate_content(
            analysis_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.3
            )
        )
        
        # Parse the JSON response
        try:
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            analysis_result = json.loads(response_text)
            
            # Validate structure
            if "overall_sentiment" not in analysis_result:
                analysis_result["overall_sentiment"] = {"compound": 0.0}
            if "key_sentences" not in analysis_result:
                analysis_result["key_sentences"] = []
            if "sentence_count" not in analysis_result:
                analysis_result["sentence_count"] = len([s for s in text.split('.') if s.strip()])
                
            # Ensure overall_sentiment has compound key
            if isinstance(analysis_result["overall_sentiment"], str):
                # Convert string sentiment to compound score
                sentiment_map = {
                    "positive": 0.5, "negative": -0.5, "neutral": 0.0,
                    "mixed": 0.0, "ambiguous": 0.0
                }
                compound_score = sentiment_map.get(analysis_result["overall_sentiment"].lower(), 0.0)
                analysis_result["overall_sentiment"] = {"compound": compound_score}
            
        except json.JSONDecodeError:
            # Fallback parsing
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            analysis_result = {
                "overall_sentiment": {"compound": 0.0},
                "key_sentences": sentences[:3] if sentences else [],
                "sentence_count": len(sentences)
            }

        logger.info("Text analysis completed successfully with Gemini API.")
        return analysis_result

    except Exception as e:
        logger.error(f"Error analyzing text with Gemini API: {str(e)}")
        # Fallback analysis
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        return {
            "overall_sentiment": {"compound": 0.0},
            "key_sentences": sentences[:3] if sentences else [],
            "sentence_count": len(sentences)
        }
