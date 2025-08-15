from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import json
from pathlib import Path

from config.config import Topic
from src.helpers.dir_helper import DirectoryHelper
from src.keyword_analyzer import KeywordAnalyzer, ScoringResult
from src.logger import LOG


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation.
    
    Attributes:
        timestamp: When this turn occurred
        speaker: Either 'user' or 'assistant'
        content: The actual message content
        score: Optional relevance score for user turns
        keyword_matches: Dictionary of matched keywords and their scores
    """
    timestamp: datetime
    speaker: str  # "user" or "assistant"
    content: str
    score: Optional[float] = None
    keyword_matches: Dict = field(default_factory=dict)

@dataclass
class ConversationSession:
    """Represents a complete conversation session on a specific topic.
    
    Attributes:
        session_id: Unique identifier for this session
        topic: The conversation topic being discussed
        start_time: When the session began
        end_time: When the session ended (None if still active)
        turns: List of all conversation turns
        final_score: Final calculated score for the session
        total_user_words: Total word count from user messages
        session_summary: Brief summary of the session
    """
    session_id: str
    topic: Topic
    start_time: datetime
    end_time: Optional[datetime] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    final_score: Optional[float] = None
    total_user_words: int = 0
    session_summary: str = ""

class ConversationManager:
    """Manages conversation sessions, scoring, and persistence.
    
    This class handles the lifecycle of conversation sessions including:
    - Starting and ending sessions
    - Adding turns and calculating scores
    - Determining when conversations should continue
    - Saving and loading conversation data
    - Generating progress reports and summaries
    """
    def __init__(self, save_conversations: bool = True):
        """Initialize the conversation manager.
        
        Args:
            save_conversations: Whether to save conversations to disk
        """
        self.current_session: Optional[ConversationSession] = None
        self.keyword_analyzer = KeywordAnalyzer()
        self.save_conversations = save_conversations
        self.conversations_dir = Path(DirectoryHelper.STORAGE_DIR + '/conversations')
        
        if save_conversations:
            self.conversations_dir.mkdir(exist_ok=True)
    
    def start_new_session(self, topic: Topic) -> str:
        """Start a new conversation session for the given topic.
        
        Args:
            topic: The topic configuration to discuss
            
        Returns:
            The unique session ID for the new session
        """
        session_id = f"{topic.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = ConversationSession(
            session_id=session_id,
            topic=topic,
            start_time=datetime.now(),
            turns=[]
        )
        
        LOG.info(f"Started new conversation session: {session_id}")
        return session_id
    
    def add_turn(self, speaker: str, content: str) -> Optional[float]:
        """Add a new turn to the current conversation session.
        
        Args:
            speaker: Either 'user' or 'assistant'
            content: The message content
            
        Returns:
            The relevance score if this was a user turn, None otherwise
            
        Raises:
            ValueError: If no active conversation session exists
        """
        if not self.current_session:
            raise ValueError("No active conversation session")
        
        turn = ConversationTurn(
            timestamp=datetime.now(),
            speaker=speaker,
            content=content
        )
        
        if speaker == "user":
            user_turns = [t.content for t in self.current_session.turns if t.speaker == "user"] + [content]
            scoring_result = self.keyword_analyzer.analyze_conversation(user_turns, self.current_session.topic)
            
            turn.score = scoring_result.total_score
            turn.keyword_matches = {k: v.relevance_score for k, v in scoring_result.keyword_matches.items()}
            
            self.current_session.total_user_words += len(content.split())
        
        self.current_session.turns.append(turn)
        
        return turn.score
    
    def get_current_score(self) -> Tuple[float, ScoringResult]:
        """Get the current conversation score and detailed results.
        
        Returns:
            Tuple of (score, scoring_result) where score is 0-100 and
            scoring_result contains detailed analysis
        """
        if not self.current_session:
            return 0.0, None
        
        user_turns = [t.content for t in self.current_session.turns if t.speaker == "user"]
        if not user_turns:
            return 0.0, None
            
        scoring_result = self.keyword_analyzer.analyze_conversation(user_turns, self.current_session.topic)
        return scoring_result.total_score, scoring_result
    
    def get_conversation_context(self, max_turns: int = 6) -> List[Dict[str, str]]:
        """Get recent conversation turns formatted for context.
        
        Args:
            max_turns: Maximum number of recent turns to include
            
        Returns:
            List of dictionaries with role, content, and timestamp
        """
        if not self.current_session:
            return []
        
        recent_turns = self.current_session.turns[-max_turns:] if len(self.current_session.turns) > max_turns else self.current_session.turns
        
        context = []
        for turn in recent_turns:
            context.append({
                "role": turn.speaker,
                "content": turn.content,
                "timestamp": turn.timestamp.isoformat()
            })
        
        return context
    
    def get_conversation_summary(self) -> str:
        """Generate a comprehensive summary of the current conversation.
        
        Returns:
            Formatted string with session statistics and progress
        """
        if not self.current_session:
            return "No active conversation"
        
        user_turns = [t.content for t in self.current_session.turns if t.speaker == "user"]
        assistant_turns = [t.content for t in self.current_session.turns if t.speaker == "assistant"]
        
        current_score, scoring_result = self.get_current_score()
        
        duration = datetime.now() - self.current_session.start_time

        summary = f"""
        Conversation Summary - Session: {self.current_session.session_id}
        Topic: {self.current_session.topic.name}
        Duration: {duration.total_seconds()/60:.1f} minutes
        Total turns: {len(self.current_session.turns)}
        User responses: {len(user_turns)}
        Current score: {current_score:.1f}/100
        Total user words: {self.current_session.total_user_words}
        """
        
        if scoring_result:
            summary += f"Topic coverage: {scoring_result.coverage_percentage:.1f}%\n"
            summary += f"Keywords mentioned: {len(scoring_result.keyword_matches)}/{len(self.current_session.topic.keywords)}\n"
        
        return summary.strip()
    
    def should_continue_conversation(self) -> Tuple[bool, str]:
        """Determine if the conversation should continue based on various criteria.
        
        Returns:
            Tuple of (should_continue, reason) where should_continue is boolean
            and reason explains the decision
        """
        if not self.current_session:
            return False, "No active session"
        
        user_turns = [t for t in self.current_session.turns if t.speaker == "user"]
        
        if len(user_turns) < 2:
            return True, "Continue - need more user input"
        
        current_score, scoring_result = self.get_current_score()
        
        if current_score >= 80:
            return False, f"Excellent coverage achieved! Score: {current_score:.1f}/100"
        
        if len(user_turns) >= 8:
            return False, f"Conversation has reached good length. Final score: {current_score:.1f}/100"
        
        duration = datetime.now() - self.current_session.start_time
        if duration > timedelta(minutes=10):
            return False, f"Time limit reached. Final score: {current_score:.1f}/100"
        
        if scoring_result and scoring_result.coverage_percentage >= 60:
            return True, f"Good progress - {scoring_result.coverage_percentage:.1f}% coverage"
        
        return True, "Continue conversation"
    
    def end_session(self) -> Optional[Dict]:
        """End the current conversation session and return session data.
        
        Returns:
            Dictionary containing complete session data, or None if no active session
        """
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        final_score, scoring_result = self.get_current_score()
        self.current_session.final_score = final_score
        
        session_data = {
            "session_id": self.current_session.session_id,
            "topic": self.current_session.topic.name,
            "start_time": self.current_session.start_time.isoformat(),
            "end_time": self.current_session.end_time.isoformat(),
            "duration_minutes": (self.current_session.end_time - self.current_session.start_time).total_seconds() / 60,
            "final_score": final_score,
            "total_turns": len(self.current_session.turns),
            "user_turns": len([t for t in self.current_session.turns if t.speaker == "user"]),
            "total_user_words": self.current_session.total_user_words,
            "turns": [
                {
                    "timestamp": turn.timestamp.isoformat(),
                    "speaker": turn.speaker,
                    "content": turn.content,
                    "score": turn.score,
                    "keyword_matches": turn.keyword_matches
                } for turn in self.current_session.turns
            ]
        }
        
        if scoring_result:
            session_data["scoring_details"] = {
                "coverage_percentage": scoring_result.coverage_percentage,
                "keyword_matches": {k: v.relevance_score for k, v in scoring_result.keyword_matches.items()},
                "detailed_breakdown": scoring_result.detailed_breakdown,
                "improvement_suggestions": self.keyword_analyzer.generate_improvement_suggestions(scoring_result, self.current_session.topic)
            }
        
        if self.save_conversations:
            self.save_session(session_data)
        
        LOG.info(f"Session ended. Final score: {final_score:.1f}/100")
        
        session_summary = session_data
        self.current_session = None
        
        return session_summary
    
    def save_session(self, session_data: Dict):
        """Save session data to a JSON file.
        
        Args:
            session_data: Dictionary containing session information to save
        """
        filename = f"{session_data['session_id']}.json"
        filepath = self.conversations_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            LOG.info(f"Conversation saved to: {filepath}")
        except Exception as e:
            LOG.error(f"Error saving conversation: {e}")
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a previously saved conversation session.
        
        Args:
            session_id: The unique identifier of the session to load
            
        Returns:
            Dictionary containing session data, or None if not found
        """
        filename = f"{session_id}.json"
        filepath = self.conversations_dir / filename
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            LOG.error(f"Error loading conversation: {e}")
            return None
    
    def list_saved_conversations(self) -> List[str]:
        """Get a list of all saved conversation session IDs.
        
        Returns:
            List of session IDs sorted by newest first
        """
        if not self.conversations_dir.exists():
            return []
        
        conversations = []
        for file in self.conversations_dir.glob("*.json"):
            conversations.append(file.stem)
        
        return sorted(conversations, reverse=True)
    
    def generate_progress_report(self) -> str:
        """Generate a detailed progress report for the current session.
        
        Returns:
            Formatted progress report with scores, coverage, and suggestions
        """
        if not self.current_session:
            return "No active conversation to report on."
        
        current_score, scoring_result = self.get_current_score()
        user_turns = [t for t in self.current_session.turns if t.speaker == "user"]
        
        report = f"""
        PROGRESS REPORT
        Current Score: {current_score:.1f}/100
        Responses Given: {len(user_turns)}
        """
        
        if scoring_result:
            report += f"Topic Coverage: {scoring_result.coverage_percentage:.1f}%\n"
            report += f"Keywords Mentioned: {len(scoring_result.keyword_matches)}\n"
            
            if scoring_result.keyword_matches:
                report += "\n Topics You've Covered:\n"
                for keyword, match in list(scoring_result.keyword_matches.items())[:5]:
                    report += f"  • {keyword.title()}: {match.relevance_score:.1f} relevance\n"
            
            suggestions = self.keyword_analyzer.generate_improvement_suggestions(scoring_result, self.current_session.topic)
            if suggestions:
                report += "\n Suggestions:\n"
                for suggestion in suggestions[:2]:
                    report += f"  • {suggestion}\n"
        
        return report.strip()