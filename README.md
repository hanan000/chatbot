# AI-Powered Speech Chatbot

An intelligent conversational AI system that engages users in role-playing conversations, monitors for specific topics and keywords, and provides scoring based on response quality and topic coverage.

## Features

- 🎤 **Speech Recognition & Synthesis**: Real-time speech-to-text and text-to-speech capabilities
- 🤖 **LLM Integration**: Powered by OpenAI's GPT models for natural conversations
- 🎯 **Keyword Analysis**: Advanced keyword detection with semantic similarity analysis
- 📊 **Real-time Scoring**: Dynamic scoring system (0-100) based on keyword relevance and coverage
- 💬 **Role-playing Conversations**: Engaging dialogues on various educational topics
- 📈 **Conversation Management**: Context tracking and session management
- 📋 **Structured Reports**: Detailed analysis reports in multiple formats

## Topics Covered

1. **Weather** - Temperature, humidity, air pressure, wind patterns, precipitation
2. **Software Application Performance** - Algorithm efficiency, hardware resources, network latency
3. **Road Traffic** - Infrastructure, traffic volume, signals, accidents, weather conditions
4. **Successful Job Interview** - Preparation, communication skills, body language, experience
5. **City Planning in Volcanic Areas** - Hazard mapping, evacuation routes, monitoring systems

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install additional system dependencies**:
   
   **For Ubuntu/Debian**:
   ```bash
   sudo apt-get install python3-pyaudio portaudio19-dev
   ```
   
   **For macOS**:
   ```bash
   brew install portaudio
   ```
   
   **For Windows**:
   ```bash
   # PyAudio should install automatically with pip
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file and add your OpenAI API key
   ```



## Configuration

### Environment Variables (.env file)

```env
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-3.5-turbo
SPEECH_RECOGNITION_TIMEOUT=5
SPEECH_PHRASE_TIMEOUT=2
```

### OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or log in
3. Generate an API key from the API section
4. Add the key to your `.env` file

## Usage

### Basic Usage

**Speech Mode (Default)**:
```bash
python main.py
```

**Text-Only Mode**:
```bash
python main.py --text
```

### Command Line Options

```bash
# Show available topics
python main.py --help-topics

# List saved conversations
python main.py --list-conversations

# Text-only mode
python main.py --text
```

## Scoring System

### How Scoring Works

- **Base Score**: Calculated from keyword weights and relevance (0-80 points)
- **Coverage Bonus**: Additional points for discussing multiple topic areas (up to 10 points)
- **Length Bonus**: Small bonus for providing detailed responses (up to 5 points)
- **Semantic Analysis**: Context and meaning analysis beyond simple keyword matching

### Score Breakdown

- **90-100**: Exceptional understanding and coverage
- **80-89**: Excellent knowledge demonstration
- **70-79**: Good grasp of the topic
- **60-69**: Satisfactory coverage
- **50-59**: Needs improvement
- **Below 50**: Poor understanding

## Project Structure

```
chatbot/
├── main.py                              # Application entry point
├── requirements.txt                     # Python dependencies
├── README.md                           # This file
├── config/
│   └── config.py                       # Topic and keyword configurations
├── src/                                # Source code directory
│   ├── chatbot.py                      # Main chatbot class
│   ├── conversation_manager.py         # Session and context management
│   ├── keyword_analyzer.py             # Keyword detection and scoring
│   ├── llm_client.py                  # OpenAI API integration
│   ├── speech_handler.py              # Speech recognition and TTS
│   ├── helpers/
│   │   └── dir_helper.py               # Directory management utilities
│   ├── logger/
│   │   ├── __init__.py
│   │   └── log.py                      # Logging configuration
│   └── utils/
│       ├── __init__.py
│       └── utils.py                    # Utility functions
├── storage/                            # Main storage directory
│   ├── conversations/                  # Saved conversation sessions (JSON)
│   └── logs/
│       └── logs.log                    # Main application logs
├── tests/                              # Test files
│   └── test_keyword_analyzer.py        # Keyword analyzer tests
└── venv/                              # Virtual environment (if created locally)
```


## Requirements

- Python 3.8+
- OpenAI API access
- Microphone and speakers (for speech mode)
- Internet connection
- ~50MB disk space for dependencies

## License

This project is created for educational purposes. Please ensure you comply with OpenAI's usage policies when using their API.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Test with `--text` mode first
4. Check your OpenAI API key and credits