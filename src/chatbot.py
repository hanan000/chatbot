import time
from typing import Optional, Dict, Tuple

from src.logger import LOG
from src.speech_handler import SpeechHandler
from src.llm_client import LLMClient
from src.conversation_manager import ConversationManager
from config.config import Topic, get_random_topic, TOPICS_CONFIG


class RolePlayChatbot:
    """
    An AI-powered conversational chatbot that engages users in role-playing conversations.
    
    This chatbot supports both speech and text modes, allows topic selection, manages
    conversation sessions, and provides scoring and feedback on user responses.
    
    Attributes:
        speech_handler (SpeechHandler): Handles speech input/output (optional).
        llm_client (LLMClient): Manages communication with the language model.
        conversation_manager (ConversationManager): Tracks conversation state and scoring.
        use_speech (bool): Whether speech functionality is enabled.
        current_topic (Topic): The current conversation topic.
        is_running (bool): Whether a conversation session is active.
    """
    DEFAULT_TIMEOUT = 15.0
    RETRY_TIMEOUT = 10.0
    PROGRESS_REPORT_INTERVAL = 1
    
    def __init__(self, api_key: str, model: str, use_speech: bool = True):
        """
        Initialize the RolePlayChatbot.
        
        Args:
            api_key (str): API key for the language model service.
            model (str): Model name to use for the language model.
            use_speech (bool): Whether to enable speech functionality. Defaults to True.
            
        Raises:
            ValueError: If api_key or model is empty or None.
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty or None")
        if not model or not model.strip():
            raise ValueError("Model cannot be empty or None")

        self.speech_handler = SpeechHandler() if use_speech else None
        self.llm_client = LLMClient(api_key, model)
        self.conversation_manager = ConversationManager()
        self.use_speech = use_speech
        self.current_topic: Optional[Topic] = None
        self.is_running = False
        
        LOG.info("AI Chatbot initialized......")
        
    def display_available_topics(self):
        """
        Display all available conversation topics to the user.
        
        Shows numbered list of topics with descriptions and includes random option.
        """
        LOG.info(" Available Topics:")
        for i, (key, topic) in enumerate(TOPICS_CONFIG.items(), 1):
            LOG.info(f"  {i}. {topic.name}")
            LOG.info(f"     {topic.description}")
        LOG.info(f"  {len(TOPICS_CONFIG) + 1}. Random Topic")
    
    def select_topic(self) -> Optional[Topic]:
        """
        Allow user to select a conversation topic via speech or text input.
        
        Returns:
            Optional[Topic]: Selected topic object, or None if selection failed.
        """
        self.display_available_topics()
        
        choice = self._get_topic_choice()
        if not choice:
            LOG.debug("No topic selected.")
            return None
        
        return self._parse_topic_choice(choice)
    
    def _get_topic_choice(self) -> Optional[str]:
        """
        Get user's topic choice via speech or text input.
        
        Returns:
            Optional[str]: User's choice, or None if no input received.
        """
        if self.use_speech:
            prompt = "Please say the number of the topic you'd like to discuss, or say 'random' for a random topic."
            return self.speech_handler.get_speech_input(prompt, timeout=self.DEFAULT_TIMEOUT)
        else:
            return input(f"Enter topic number (1-{len(TOPICS_CONFIG) + 1}) or 'random': ").strip()
    
    def _parse_topic_choice(self, choice: str) -> Optional[Topic]:
        """
        Parse user's topic choice and return corresponding topic.
        
        Args:
            choice (str): User's input choice.
            
        Returns:
            Optional[Topic]: Selected topic, or None if invalid choice.
        """
        choice = choice.lower().strip()
        
        if 'random' in choice or choice == str(len(TOPICS_CONFIG) + 1):
            topic = get_random_topic()
            LOG.info(f"Random topic selected: {topic.name}")
            return topic
        
        try:
            topic_num = int(''.join(filter(str.isdigit, choice)))
            if 1 <= topic_num <= len(TOPICS_CONFIG):
                topic = list(TOPICS_CONFIG.values())[topic_num - 1]
                LOG.info(f"Selected topic: {topic.name}")
                return topic
            else:
                LOG.warning(f"Invalid topic number. Please choose 1-{len(TOPICS_CONFIG) + 1}")
                return None
        except (ValueError, IndexError, TypeError) as e:
            LOG.error(f"Invalid input for topic selection: {e}")
            return None
    
    def initialize_conversation(self, topic: Topic):
        """
        Initialize a new conversation session with the given topic.
        
        Args:
            topic (Topic): The topic to use for the conversation.
            
        Sets up the LLM persona, starts session tracking, and delivers opening message.
        """
        self.current_topic = topic
        self.conversation_manager.start_new_session(topic)
        
        persona_prompt = self.llm_client.create_roleplay_persona(topic)
        self.llm_client.set_system_prompt(persona_prompt)
        
        LOG.info(f" Starting conversation about: {topic.name}")
        LOG.info(f"Topic: {topic.description}")
        
        opening_message = topic.introduction
        self._deliver_message(opening_message)
        self.conversation_manager.add_turn("assistant", opening_message)
    
    def _deliver_message(self, message: str):
        """
        Deliver a message to the user via text log and optionally speech.
        
        Args:
            message (str): The message to deliver.
        """
        LOG.info(f" AI: {message}")
        if self.use_speech and self.speech_handler:
            self.speech_handler.speak(message)
            time.sleep(0.5)
    
    def _get_user_input(self) -> Optional[str]:
        """
        Get user input via speech or text.
        
        Returns:
            Optional[str]: User input string, or None if interrupted.
        """
        if self.use_speech and self.speech_handler:
            return self.speech_handler.get_speech_input("", timeout=self.DEFAULT_TIMEOUT)
        else:
            try:
                return input(" USER: ").strip()
            except KeyboardInterrupt:
                return None
    
    def handle_user_response(self, user_input: str) -> bool:
        """
        Process user input and generate appropriate response.
        
        Args:
            user_input (str): The user's input message.
            
        Returns:
            bool: True if conversation should continue, False if it should end.
        """
        if not user_input:
            return True
        
        LOG.info(f"USER: {user_input}")
        
        score = self.conversation_manager.add_turn("user", user_input)
        
        current_score, scoring_result = self.conversation_manager.get_current_score()
        
        if len([t for t in self.conversation_manager.current_session.turns if t.speaker == "user"]) % self.PROGRESS_REPORT_INTERVAL == 0:
            progress = self.conversation_manager.generate_progress_report()
            LOG.info(f"{progress}")

        should_continue, reason = self.conversation_manager.should_continue_conversation()
        
        if not should_continue:
            final_response = f"That's a great discussion! {reason}Thank you for sharing your insights about {self.current_topic.name}!"
            self._deliver_message(final_response)
            return False

        try:
            if scoring_result:
                llm_response = self.llm_client.generate_follow_up_question(
                    self.current_topic, user_input, current_score
                )
            else:
                llm_response = self.llm_client.generate_response(user_input)
            
            if llm_response:
                self._deliver_message(llm_response)
                self.conversation_manager.add_turn("assistant", llm_response)
            else:
                fallback = "That's interesting! Can you tell me more about what you think influences this the most?"
                self._deliver_message(fallback)
                self.conversation_manager.add_turn("assistant", fallback)
                
        except Exception as e:
            LOG.error(f"Error generating response: {e}")
            fallback = "I'd love to hear more about your thoughts on this topic!"
            self._deliver_message(fallback)

        return True
    
    def run_conversation(self):
        """
        Main conversation loop that handles topic selection and user interaction.
        
        Manages the complete conversation flow including topic selection,
        initialization, user interaction loop, and session cleanup.
        """
        LOG.info("Welcome to the AI-Powered Speech Chatbot!")
        LOG.info("This chatbot will engage you in role-playing conversations and score your responses.")
        
        if self.use_speech:
            if not self.speech_handler.test_audio_system():
                LOG.error("Audio system test failed. Switching to text mode.")
                self.use_speech = False
        
        if not self.llm_client.test_connection():
            LOG.error("Cannot connect to LLM service. Please check your API key and internet connection.")
            return
        
        while True:
            topic = self.select_topic()
            if not topic:
                if self._ask_retry("Invalid topic selection. Would you like to try again?"):
                    continue
                else:
                    break
            
            self.initialize_conversation(topic)
            self.is_running = True
            conversation_count = 0
            
            try:
                while self.is_running:
                    user_input = self._get_user_input()
                    
                    if user_input is None:
                        LOG.exception("Conversation interrupted by user.")
                        break
                    
                    if user_input.lower().strip() in ['quit', 'exit', 'stop', 'end']:
                        LOG.exception("Ending conversation as requested.")
                        break
                    
                    if not user_input.strip():
                        LOG.error(" No input received. Please try speaking again.")
                        continue
                    
                    conversation_count += 1
                    should_continue = self.handle_user_response(user_input)
                    
                    if not should_continue:
                        self.is_running = False
                        
            except KeyboardInterrupt:
                LOG.exception("Conversation interrupted by user.")
            except Exception as e:
                LOG.error(f"An error occurred: {e}")
            
            session_data = self.conversation_manager.end_session()
            self.display_final_results(session_data)
            
            if not self._ask_retry("Would you like to start a new conversation on a different topic?"):
                break
        
        LOG.info("Thank you for using the AI Chatbot! Goodbye!")
        if self.use_speech and self.speech_handler:
            self.speech_handler.cleanup()
    
    def _ask_retry(self, question: str) -> bool:
        """
        Ask user a yes/no question via speech or text.
        
        Args:
            question (str): The question to ask the user.
            
        Returns:
            bool: True if user answered affirmatively, False otherwise.
        """
        if self.use_speech and self.speech_handler:
            response = self.speech_handler.get_speech_input(f"{question} Say 'yes' or 'no'.", timeout=self.RETRY_TIMEOUT)
        else:
            response = input(f"{question} (y/n): ").strip().lower()
        
        if not response:
            return False
        
        return 'yes' in response.lower() or response.lower() in ['y', 'yeah', 'yep', 'sure']
    
    def display_final_results(self, session_data: Optional[Dict]):
        """
        Display comprehensive results from a completed conversation session.
        
        Args:
            session_data (Optional[Dict]): Session data containing scores,
                                          keywords, and performance metrics.
        """
        if not session_data:
            LOG.debug(" No session data available.")
            return

        LOG.info("📊 FINAL CONVERSATION RESULTS")
        
        LOG.info(f"Topic: {session_data['topic']}")
        LOG.info(f"Duration: {session_data['duration_minutes']:.1f} minutes")
        LOG.info(f"Your responses: {session_data['user_turns']}")
        LOG.info(f"Total words: {session_data['total_user_words']}")
        LOG.info(f"Final Score: {session_data['final_score']:.1f}/100")
        
        if 'scoring_details' in session_data:
            details = session_data['scoring_details']
            LOG.info(f"Topic Coverage: {details['coverage_percentage']:.1f}%")
            LOG.info(f"Keywords mentioned: {len(details['keyword_matches'])}")
            
            if details['keyword_matches']:
                LOG.info("Topics you covered:")
                for keyword, relevance in list(details['keyword_matches'].items())[:5]:
                    LOG.info(f"  • {keyword.title()}: {relevance:.1f} relevance")
            
            if details['improvement_suggestions']:
                LOG.info("Areas for improvement:")
                for suggestion in details['improvement_suggestions']:
                    LOG.info(f"  • {suggestion}")

    
    def run_text_only_mode(self):
        """
        Run the chatbot in text-only mode without speech functionality.
        
        Disables speech handlers and runs the conversation in text mode only.
        """
        LOG.info("Running in text-only mode (no speech)")
        self.use_speech = False
        self.speech_handler = None
        self.run_conversation()

