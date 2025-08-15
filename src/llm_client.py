from openai import OpenAI
from typing import List, Dict, Optional
from dataclasses import dataclass
from config.config import Topic
from src.logger import LOG
from src.utils import get_conf


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation.
    
    Attributes:
        role: The message sender ("user", "assistant", or "system")
        content: The actual message text
        timestamp: Optional timestamp for when the message was created
    """
    role: str
    content: str
    timestamp: float = None

class LLMClient:
    """Client for interacting with OpenAI's language models.
    
    This class manages conversations with OpenAI's API, including maintaining
    conversation history, generating responses, and creating specialized prompts
    for different conversation scenarios.
    """
    def __init__(self, api_key: str, model: str = get_conf("MODEL_NAME")):
        """Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key for authentication
            model: Model name to use (defaults to configured MODEL_NAME)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.conversation_history: List[ConversationMessage] = []
        self.system_prompt = ""
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the conversation.
        
        Args:
            prompt: System prompt that defines the AI's behavior
        """
        self.system_prompt = prompt
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history.
        
        Args:
            role: Message role ("user", "assistant", or "system")
            content: The message content
        """
        message = ConversationMessage(role=role, content=content)
        self.conversation_history.append(message)
    
    def clear_history(self):
        """Clear all conversation history."""
        self.conversation_history = []
    
    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get conversation context formatted for OpenAI API.
        
        Args:
            max_messages: Maximum number of recent messages to include
            
        Returns:
            List of message dictionaries formatted for OpenAI API
        """
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        recent_messages = self.conversation_history[-max_messages:] if len(self.conversation_history) > max_messages else self.conversation_history
        
        for msg in recent_messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        return messages
    
    def generate_response(self, user_input: str, temperature:
    float = get_conf('TEMPERATURE', 0.7),
    max_tokens: int = get_conf('MAX_TOKENS', 500)) -> Optional[str]:
        """Generate an AI response to user input.
        
        Args:
            user_input: The user's message
            temperature: Creativity level (0.0-2.0, higher = more creative)
            max_tokens: Maximum response length
            
        Returns:
            AI-generated response string, or None if error occurred
        """
        try:
            self.add_message("user", user_input)
            
            messages = self.get_conversation_context()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=int(get_conf('TOP_P', 1)),
                frequency_penalty=0,
                presence_penalty=0
            )
            
            assistant_response = response.choices[0].message.content.strip()
            self.add_message("assistant", assistant_response)
            
            return assistant_response
            
        except Exception as e:
            LOG.error(f"Error generating LLM response: {e}")
            return None
    
    def generate_follow_up_question(self, topic: Topic, user_response: str, current_score: float) -> str:
        """Generate a contextual follow-up question based on conversation progress.
        
        Creates questions that acknowledge the user's response while guiding them
        toward unexplored topic areas to improve conversation coverage.
        
        Args:
            topic: The conversation topic with keywords and descriptions
            user_response: The user's most recent message
            current_score: Current conversation score (0-100)
            
        Returns:
            Generated follow-up question string
        """
        prompt = f"""
        You are having a conversation about {topic.name}. The user just said: "{user_response}"
        
        Current conversation score based on keyword coverage: {current_score:.1f}/100
        
        Key areas that should be covered in this topic:
        {chr(10).join([f"- {kw.term}: {kw.description}" for kw in topic.keywords[:8]])}
        
        Generate a natural follow-up question that:
        1. Acknowledges what the user said
        2. Encourages them to elaborate on areas they haven't fully covered
        3. Sounds conversational and engaging
        4. Helps guide them toward the key concepts if they're missing them
        
        Keep it under 50 words and make it sound like a curious friend asking for more details.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=float(get_conf('FOLLOW_UP_Q_TEP')),
                max_tokens=int(get_conf('FOLLOW_UP_Q_MAX_TOKENS'))
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            LOG.error(f"Error generating follow-up question: {e}")
            return "That's interesting! Can you tell me more about what you think influences this the most?"
    
    def create_roleplay_persona(self, topic: Topic) -> str:
        """Create a system prompt for topic-specific roleplay conversations.
        
        Generates a detailed persona prompt that defines the AI's personality,
        knowledge focus, and conversation style for a specific topic.
        
        Args:
            topic: Topic configuration with keywords and descriptions
            
        Returns:
            Complete system prompt for roleplay conversations
        """
        persona_prompt = f"""
        You are an enthusiastic and knowledgeable conversation partner who loves discussing {topic.name}. 
        
        Your personality traits:
        - Curious and engaging
        - Knowledgeable but not condescending  
        - Asks thoughtful follow-up questions
        - Shares interesting insights when appropriate
        - Encourages the user to share their thoughts and experiences
        
        Topic focus: {topic.description}
        
        Key areas you're interested in discussing:
        {chr(10).join([f"- {kw.term}: {kw.description}" for kw in topic.keywords[:6]])}
        
        Your goal is to have a natural, engaging conversation while gently guiding the discussion to cover these key areas. You should respond conversationally and show genuine interest in what the user says.
        
        Always:
        - Keep responses under 100 words
        - Ask one follow-up question per response
        - Acknowledge what the user said before asking more
        - Be encouraging and positive
        """
        
        return persona_prompt
    
    def test_connection(self) -> bool:
        """Test the connection to OpenAI API.
        
        Sends a simple test message to verify API connectivity and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, this is a test. Please respond with 'Connection successful'."}],
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            return "successful" in result.lower()
            
        except Exception as e:
            LOG.error(f"LLM connection test failed: {e}")
            return False