import argparse
import sys
from pathlib import Path

from src.chatbot import RolePlayChatbot
from config.config import TOPICS_CONFIG
from src.helpers.dir_helper import DirectoryHelper
from src.logger import LOG
from src.utils import get_conf


def create_directories():

    Path(DirectoryHelper.STORAGE_DIR + '/storage').mkdir(exist_ok=True)
    LOG.info("Created storage directory for saving data")

def display_banner():
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 AI CHATBOT 💬🎤                         ║
║                                                              ║
║  An AI-powered role-playing chatbot that evaluates your     ║
║  knowledge through conversations                             ║
║                                                              ║
║  Features:                                                   ║
║  • Text and Speech input modes                              ║
║  • Role-playing conversations on various topics             ║
║  • Real-time keyword analysis and scoring                   ║
║  • Conversation context management                          ║
║  • Structured output and detailed reports                   ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def display_help():
    help_text = """
    AVAILABLE TOPICS:"""
    for i, (key, topic) in enumerate(TOPICS_CONFIG.items(), 1):
        help_text += f"  {i}. {topic.name}\n"
        help_text += f"     {topic.description}\n\n"
    
    help_text += """
    HOW TO USE:
    1. Choose your input mode (Text or Speech)
    2. Choose a topic from the list
    3. Have a natural conversation about the topic
    4. The chatbot will ask follow-up questions
    5. Your responses are analyzed for keyword coverage
    6. Get a score (0-100) based on your knowledge demonstration
    
    TEXT MODE:
    - Type your responses directly
    - Type "quit", "exit", "stop", or "end" to finish
    
    SPEECH MODE:
    - Speak your responses naturally
    - Say "quit", "exit", "stop", or "end" to finish the conversation
    - Use Ctrl+C to interrupt at any time
    
    SCORING SYSTEM:
    - Keywords are weighted based on importance
    - Semantic analysis considers context and relevance
    - Coverage bonus for discussing multiple aspects
    - Final score reflects depth and breadth of knowledge
    
    TIPS FOR BETTER SCORES:
    - Discuss multiple aspects of the topic
    - Use technical terminology when appropriate
    - Provide specific examples and details
    - Explain relationships between concepts
    """
    print(help_text)

def select_input_mode():
    """Interactive mode selection when no command line arguments are provided"""
    LOG.info("SELECT INPUT MODE")
    
    while True:
        LOG.info("Choose your preferred input mode:")
        LOG.info("1. Text Mode - Type your responses")
        LOG.info("2. Speech Mode - Speak your responses (requires microphone)")
        LOG.info("3. Help - Show detailed information")
        LOG.info("4. Exit")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                LOG.info("Text mode selected")
                return True  # text_mode = True
            elif choice == "2":
                LOG.info("Speech mode selected")
                return False  # text_mode = False
            elif choice == "3":
                display_help()
                continue
            elif choice == "4":
                LOG.info("Goodbye!")
                sys.exit(0)
            else:
                LOG.info("Invalid choice. Please enter 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            LOG.error("Application interrupted by user. Goodbye!")
            sys.exit(0)
        except Exception:
            LOG.error("Invalid input. Please try again.")

def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Chatbot for Knowledge Evaluation",
        epilog="""
        Examples:
          python main.py                    # Interactive mode selection
          python main.py --text             # Force text input mode
          python main.py --help-topics      # Show available topics
          python main.py --list-conversations  # List saved sessions
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--text", 
        action="store_true",
        help="Run in text-only mode (no speech recognition/synthesis)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="OpenAI model to use (default: gpt-3.5-turbo)"
    )
    
    parser.add_argument(
        "--help-topics",
        action="store_true",
        help="Display detailed information about available topics"
    )
    
    parser.add_argument(
        "--list-conversations",
        action="store_true",
        help="List saved conversation sessions"
    )
    
    args = parser.parse_args()
    
    if args.help_topics:
        display_help()
        return
    
    display_banner()
    
    if args.list_conversations:
        from src.conversation_manager import ConversationManager
        cm = ConversationManager()
        conversations = cm.list_saved_conversations()
        
        if conversations:
            LOG.info("Saved Conversations Successfully")
        else:
            LOG.exception("No saved conversations found.")
        return

    create_directories()

    if args.text:
        text_mode = True
        LOG.info(f"Model: {args.model}")
        LOG.info("Mode: Text Input")
    else:
        import sys
        if len(sys.argv) == 1:  # No arguments provided
            text_mode = select_input_mode()
        else:
            text_mode = False
        
    LOG.info(f"Model: {args.model}")
    LOG.info(f"{'💬' if text_mode else '🎤'} Mode: {'Text' if text_mode else 'Speech'} Input")
    
    try:
        chatbot = RolePlayChatbot(
            api_key=get_conf("OPENAI_API_KEY"),
            model=get_conf('MODEL_NAME'),
            use_speech=not text_mode
        )
        if text_mode:
            chatbot.run_text_only_mode()
        else:
            chatbot.run_conversation()
            
    except KeyboardInterrupt:
        LOG.info("Application interrupted by user. Goodbye!")
    except Exception as e:
        LOG.error(f"An unexpected error occurred: {e}")
        LOG.error("Please check your configuration and try again.")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()