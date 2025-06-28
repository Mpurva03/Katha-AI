# 🎭 KATHA-AI: A AI Story Generator

A powerful web application that generates creative stories with AI-powered text, images, and audio using multiple AI services including Google Gemini, Hugging Face, Stability AI, and OpenAI.

![AI Story Generator](https://img.shields.io/badge/AI-Story%20Generator-blue?style=for-the-badge&logo=openai)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3+-red?style=for-the-badge&logo=flask)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=for-the-badge&logo=javascript)

## ✨ Features

- **📚 Story Generation**: Create engaging stories using Google Gemini AI
- **🖼️ Image Generation**: Generate beautiful illustrations with Hugging Face Stable Diffusion or Stability AI
- **🔊 Audio Generation**: Convert stories to speech using OpenAI Text-to-Speech
- **🎨 Multiple Genres**: Fantasy, Sci-Fi, Mystery, Romance, Horror, Adventure, Comedy, Drama
- **🎭 Various Tones**: Adventurous, Mysterious, Romantic, Humorous, Dark, Whimsical, Serious, Uplifting
- **📏 Customizable Length**: 100-2000 words
- **🌙 Dark/Light Theme**: Toggle between themes with system preference detection
- **📱 Responsive Design**: Works on desktop and mobile devices
- **💾 Export Options**: Copy, download, and share generated stories
- **🔄 Fallback Systems**: Multiple AI service providers for reliability

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- API keys for the services you want to use

### Installation

1. **Clone the repository**
   \`\`\`bash
   git clone https://github.com/yourusername/ai-story-generator.git
   cd ai-story-generator
   \`\`\`

2. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Set up environment variables**
   
   Create a \`.env\` file in the project root:
   \`\`\`env
   ## For story generation
   GEMINI_API_KEY=your_gemini_api_key_here
   
   ## For audio generation
   OPENAI_API_KEY=your_openai_api_key_here
   
   ##For image generation
   HUGGINGFACE_API_TOKEN=your_huggingface_token_here
   
   STABILITY_API_KEY=your_stability_api_key_here
   
   ## Flask configuration
   FLASK_ENV=development
   PORT=5500
   \`\`\`

5. **Start the backend server**
   \`\`\`bash
   python app.py
   \`\`\`

6. **Open the frontend**
   
   Open \`index.html\` in your web browser or serve it with a local web server.

## 🔑 API Keys Setup

### Required APIs

#### Google Gemini API (Required)
- **Purpose**: Story generation and text analysis
- **Get API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Free Tier**: Available with generous limits

### Optional APIs

#### OpenAI API (Optional - for audio)
- **Purpose**: Text-to-speech conversion
- **Get API Key**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Pricing**: Pay-per-use, very affordable for TTS

#### Hugging Face API (Optional - for images)
- **Purpose**: Image generation using Stable Diffusion
- **Get API Token**: [Hugging Face Tokens](https://huggingface.co/settings/tokens)
- **Free Tier**: Available with rate limits

#### Stability AI API (Optional - for images)
- **Purpose**: High-quality image generation
- **Get API Key**: [Stability AI Platform](https://platform.stability.ai/)
- **Pricing**: Pay-per-use

## 🏗️ Project Structure

\`\`\`
ai-story-generator/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── script.js             # Frontend JavaScript
├── index.html            # Frontend HTML (not included, create your own)
├── utils/                # Utility modules
│   ├── story_generator.py    # Story generation with Gemini
│   ├── image_generator.py    # Image generation with multiple providers
│   ├── audio_generator.py    # Audio generation with OpenAI
│   └── text_analysis.py     # Text analysis with Gemini
├── temp/                 # Generated content storage
│   ├── stories/          # Generated stories
│   ├── images/           # Generated images
│   └── audio/            # Generated audio files
└── README.md             # This file
\`\`\`

### Service Fallbacks

The application includes intelligent fallback systems:

- **Image Generation**: Hugging Face → Stability AI → Disabled
- **Story Generation**: Gemini (required)
- **Audio Generation**: OpenAI TTS (optional)

## 📖 Usage

1. **Start the Backend**: Run \`python app.py\`
2. **Open Frontend**: Open your HTML file in a browser
3. **Enter Story Prompt**: Describe what story you want
4. **Select Options**: Choose genre, tone, length, and generation options
5. **Generate**: Click "Generate Story" and wait for the magic!

### Example Prompts

- "A young wizard discovers a hidden library in an ancient castle"
- "In a cyberpunk city, a detective investigates mysterious disappearances"
- "Two rival chefs compete in a cooking competition with magical ingredients"
- "A time traveler gets stuck in the Victorian era"

## 🛠️ API Endpoints

### Story Generation
\`\`\`
POST /api/generate-story
Content-Type: application/json

{
  "prompt": "Your story idea",
  "genre": "fantasy",
  "tone": "adventurous", 
  "length": 500,
  "generateImage": true,
  "generateAudio": false
}
\`\`\`

### Audio Generation
\`\`\`
POST /api/generate-audio
Content-Type: application/json

{
  "text": "Story text to convert to speech",
  "storyId": "unique-story-id"
}
\`\`\`

### Health Check
\`\`\`
GET /api/health
\`\`\`

### File Serving
\`\`\`
GET /api/image/<filename>
GET /api/audio/<filename>
\`\`\`

## 🔍 Troubleshooting

### Common Issues

#### "Backend connection error"
- **Solution**: Make sure Flask server is running on port 5500
- **Check**: Run \`python app.py\` and look for startup messages
- **Verify**: Visit \`http://localhost:5500/api/health\` in browser

#### "Gemini API key not configured"
- **Solution**: Add \`GEMINI_API_KEY\` to your \`.env\` file
- **Get Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)

#### "Image generation failed"
- **Solution**: Add \`HUGGINGFACE_API_TOKEN\` or \`STABILITY_API_KEY\` to \`.env\`
- **Alternative**: Images are optional, story generation will still work

#### "Audio generation not available"
- **Solution**: Add \`OPENAI_API_KEY\` to your \`.env\` file
- **Alternative**: Audio is optional, you can generate it separately

### Debug Mode

Enable debug logging by setting:
\`\`\`env
FLASK_ENV=development
\`\`\`

Check the console output and \`app.log\` file for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (\`git checkout -b feature/amazing-feature\`)
3. Commit your changes (\`git commit -m 'Add amazing feature'\`)
4. Push to the branch (\`git push origin feature/amazing-feature\`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini** for powerful story generation
- **Hugging Face** for accessible AI image generation
- **Stability AI** for high-quality image generation
- **OpenAI** for excellent text-to-speech capabilities
- **Flask** for the robust web framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Look at existing [Issues](https://github.com/yourusername/ai-story-generator/issues)
3. Create a new issue with detailed information

## 🔮 Future Features

- [ ] User accounts and story saving
- [ ] Story templates and prompts library
- [ ] Multiple voice options for audio
- [ ] Story sharing and community features
- [ ] Advanced story editing tools
- [ ] Integration with more AI providers
- [ ] Mobile app version

---

*Generate amazing stories with the power of artificial intelligence!*
\`\`\`

