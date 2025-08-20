import time

from src.logger import LOG
from src.speech_handler import SpeechHandler
from src.llm_client import LLMClient
from src.conversation_manager import ConversationManager
from config.config import get_random_topic, TOPICS_CONFIG


class RolePlayChatbot:
    """
    Simple AI chatbot for educational conversations with scoring.
    """
    
    def __init__(self, api_key: str, model: str, use_speech: bool = True):
        """Initialize the chatbot with API credentials and speech settings.
        
        Args:
            api_key: OpenAI API key for LLM access
            model: Model name to use (e.g., 'gpt-3.5-turbo')
            use_speech: Enable speech input/output functionality
        """
        self.speech_handler = SpeechHandler() if use_speech else None
        self.llm_client = LLMClient(api_key, model)
        self.conversation_manager = ConversationManager()
        self.use_speech = use_speech
        self.current_topic = None
        LOG.info("AI Chatbot initialized")
    
        
    def show_topics(self):
        """Display all available conversation topics to the user.
        
        Shows a numbered list of available topics plus random option.
        """
        LOG.info("Available Topics:")
        for i, topic in enumerate(TOPICS_CONFIG.values(), 1):
            LOG.info(f"  {i}. {topic.name}")
        LOG.info(f"  {len(TOPICS_CONFIG) + 1}. Random Topic")
    
    def get_topic(self):
        """Get user's topic selection via speech or text input.

        Returns:
            Topic: Selected topic object, or None if selection failed
        """
        self.show_topics()
        
        if self.use_speech:
            choice = self.speech_handler.get_speech_input(
                "Say the number of the topic you'd like to discuss", timeout=15
            )
        else:
            choice = input("Enter topic number: ").strip()
        
        if not choice:
            return None
            
        if 'random' in choice.lower() or choice == str(len(TOPICS_CONFIG) + 1):
            return get_random_topic()
            
        try:
            num = int(choice)
            if 1 <= num <= len(TOPICS_CONFIG):
                return list(TOPICS_CONFIG.values())[num - 1]
        except ValueError:
            pass
            
        LOG.warning("Invalid topic selection")
        return None
    
    
    def start_conversation(self, topic):
        """Initialize a new conversation session with the given topic.
        
        Args:
            topic: Topic object containing keywords and introduction
        """
        self.current_topic = topic
        self.conversation_manager.start_new_session(topic)
        
        persona_prompt = self.llm_client.create_roleplay_persona(topic)
        self.llm_client.set_system_prompt(persona_prompt)
        
        LOG.info(f"Starting conversation: {topic.name}")
        
        self.send_message(topic.introduction)
        self.conversation_manager.add_turn("assistant", topic.introduction)
    
    def send_message(self, message):
        """Send a message to the user via text log and optionally speech.
        
        Args:
            message (str): Message to deliver to user
        """
        LOG.info(f"AI: {message}")
        if self.use_speech and self.speech_handler:
            self.speech_handler.speak(message)
            time.sleep(0.5)
    
    def get_user_input(self):
        """Get user input via speech or text.

        Returns:
            str: User input string, or None if interrupted
        """
        if self.use_speech and self.speech_handler:
            return self.speech_handler.get_speech_input("", timeout=15)
        else:
            try:
                return input("USER INPUT: ").strip()
            except KeyboardInterrupt:
                return None
    
    def handle_response(self, user_input):
        """Process user input and generate appropriate AI response.

        Args:
            user_input (str): The user's input message

        Returns:
            bool: True if conversation should continue, False if it should end
        """
        if not user_input:
            return True
        
        LOG.info(f"USER: {user_input}")
        
        self.conversation_manager.add_turn("user", user_input)
        current_score, _ = self.conversation_manager.get_current_score()
        
        should_continue, reason = self.conversation_manager.should_continue_conversation()
        
        if not should_continue:
            final_message = f"Great discussion! {reason}Thanks for talking about {self.current_topic.name}!"
            self.send_message(final_message)
            return False

        try:
            llm_response = self.llm_client.generate_follow_up_question(
                self.current_topic, user_input, current_score
            )
            
            if llm_response:
                self.send_message(llm_response)
                self.conversation_manager.add_turn("assistant", llm_response)
            else:
                fallback = "That's interesting! Can you tell me more about what you think influences this the most?"
                self.send_message(fallback)
                self.conversation_manager.add_turn("assistant", fallback)
                
        except Exception as e:
            LOG.error(f"Error: {e}")
            self.send_message("I'd love to hear more about your thoughts on this topic!")

        return True
    
    def run_conversation(self):
        """Main conversation loop handling topic selection and user interaction.
        
        Manages complete conversation flow including topic selection,
        initialization, user interaction loop, and session cleanup.
        """
        LOG.info("Welcome to the AI Chatbot!")
        
        if self.use_speech and not self.speech_handler.test_audio_system():
            LOG.error("Audio test failed. Using text mode.")
            self.use_speech = False
        
        if not self.llm_client.test_connection():
            LOG.error("Cannot connect to AI service.")
            return
        
        while True:
            topic = self.get_topic()
            if not topic:
                if self.ask_yes_no("Try again?"):
                    continue
                else:
                    break
            
            self.start_conversation(topic)
            
            try:
                while True:
                    user_input = self.get_user_input()
                    
                    if not user_input:
                        break
                    
                    exit_words = ['quit', 'exit', 'stop', 'end']
                    if any(word in user_input.lower() for word in exit_words):
                        LOG.info("Conversation ended.")
                        break
                    
                    if not self.handle_response(user_input):
                        break
                        
            except KeyboardInterrupt:
                LOG.info("Interrupted by user.")
            except Exception as e:
                LOG.error(f"Error: {e}")
            
            session_data = self.conversation_manager.end_session()
            self.show_results(session_data)
            
            if not self.ask_yes_no("Start new conversation?"):
                break
        
        LOG.info("Goodbye!")
        if self.use_speech and self.speech_handler:
            self.speech_handler.cleanup()
    
    def ask_yes_no(self, question):
        """Ask user a yes/no question via speech or text.
        
        Args:
            question (str): Question to ask the user
            
        Returns:
            bool: True if user answered affirmatively, False otherwise
        """
        if self.use_speech and self.speech_handler:
            response = self.speech_handler.get_speech_input(f"{question} Say yes or no.", timeout=10)
        else:
            response = input(f"{question} (y/n): ").strip().lower()
        
        if not response:
            return False
        
        return 'yes' in response.lower() or response.lower() in ['y', 'yeah', 'yep', 'sure']
    
    def show_results(self, session_data):
        """Display conversation results and scoring information.
        
        Args:
            session_data (dict): Session data containing scores and metrics
        """
        if not session_data:
            return

        LOG.info("CONVERSATION RESULTS")
        LOG.info(f"Topic: {session_data['topic']}")
        LOG.info(f"Duration: {session_data['duration_minutes']:.1f} minutes")
        LOG.info(f"Score: {session_data['final_score']:.1f}/100")
        
        if 'scoring_details' in session_data:
            details = session_data['scoring_details']
            if details['keyword_matches']:
                LOG.info("Topics covered:")
                for keyword in list(details['keyword_matches'].keys())[:3]:
                    LOG.info(f"  • {keyword.title()}")

    
    def run_text_only_mode(self):
        """Run the chatbot in text-only mode without speech functionality.
        
        Disables speech handlers and runs conversation in text mode only.
        """
        LOG.info("Running in text-only mode (no speech)")
        self.use_speech = False
        self.speech_handler = None
        self.run_conversation()

