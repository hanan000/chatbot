import re
from typing import Dict, List
from dataclasses import dataclass
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from config.config import Topic, Keyword
from src.logger import LOG
from src.utils import get_conf


@dataclass
class KeywordMatch:
    """Represents a match for a specific keyword in analyzed text.
    
    Attributes:
        keyword: The original keyword configuration that was matched
        occurrences: Number of times the keyword appeared
        contexts: List of text snippets containing the keyword
        relevance_score: AI-calculated relevance score (0.0-1.0)
    """
    keyword: Keyword
    occurrences: int
    contexts: List[str]
    relevance_score: float

@dataclass
class ScoringResult:
    """Contains the complete analysis results for a text/conversation.
    
    Attributes:
        total_score: Overall score from 0-100
        keyword_matches: Dictionary mapping keyword terms to their matches
        coverage_percentage: Percentage of topic keywords that were covered
        detailed_breakdown: Detailed scoring breakdown for each keyword
    """
    total_score: float
    keyword_matches: Dict[str, KeywordMatch]
    coverage_percentage: float
    detailed_breakdown: Dict[str, float]

class KeywordAnalysis(BaseModel):
    """Structure for LangChain keyword analysis output"""
    matched_keywords: List[str] = Field(description="List of keywords found in the text")
    relevance_scores: Dict[str, float] = Field(description="Relevance score for each keyword (0.0-1.0)")
    contexts: Dict[str, List[str]] = Field(description="Context snippets where keywords appear")
    semantic_matches: List[str] = Field(description="Keywords found through semantic similarity")

class KeywordAnalyzer:
    """Analyzes text for keyword presence and calculates relevance scores.
    
    This class combines traditional keyword matching with AI-powered semantic
    analysis to evaluate how well text covers a given topic. It uses LangChain
    and OpenAI to perform sophisticated text analysis beyond simple string matching.
    """
    def __init__(self):
        """Initialize the keyword analyzer with LLM and parsing components."""
        self.llm = ChatOpenAI(model=get_conf('MODEL_NAME'),api_key=get_conf('OPENAI_API_KEY'), temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=KeywordAnalysis)
        self.setup_prompt_template()
    
    def setup_prompt_template(self):
        """Configure the LangChain prompt template for keyword analysis."""
        template = """
        You are a keyword analysis expert. Analyze the given text for the presence of specific keywords and their semantic variations.

        TARGET KEYWORDS: {keywords}
        KEYWORD DESCRIPTIONS: {descriptions}

        TEXT TO ANALYZE: {text}

        Instructions:
        1. Find exact matches and semantic variations of the target keywords
        2. Calculate relevance scores (0.0-1.0) based on context and semantic similarity
        3. Extract context snippets (10-20 words) around each keyword occurrence
        4. Identify semantic matches even when exact terms aren't present

        {format_instructions}
        """
        
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm | self.parser
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text for keyword matching.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            Cleaned text with normalized whitespace and punctuation
        """
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_keyword_contexts(self, text: str, keyword: str, context_window: int = 10) -> List[str]:
        """Extract context snippets around keyword occurrences.
        
        Args:
            text: Text to search for keywords
            keyword: Specific keyword to find
            context_window: Number of words to include before/after keyword
            
        Returns:
            List of context snippets containing the keyword
        """
        words = text.split()
        keyword_words = keyword.split()
        contexts = []
        
        for i in range(len(words) - len(keyword_words) + 1):
            if ' '.join(words[i:i+len(keyword_words)]) == keyword:
                start = max(0, i - context_window)
                end = min(len(words), i + len(keyword_words) + context_window)
                context = ' '.join(words[start:end])
                contexts.append(context)
        
        return contexts
    
    def analyze_with_langchain(self, text: str, keywords: List[Keyword]) -> KeywordAnalysis:
        """Perform AI-powered semantic analysis of text for keywords.
        
        Args:
            text: Text to analyze
            keywords: List of keyword configurations to search for
            
        Returns:
            KeywordAnalysis containing matched keywords and relevance scores
        """
        try:
            keyword_terms = [kw.term for kw in keywords]
            keyword_descriptions = [kw.description for kw in keywords]
            
            result = self.chain.invoke({
                "text": text,
                "keywords": ", ".join(keyword_terms),
                "descriptions": " | ".join([f"{term}: {desc}" for term, desc in zip(keyword_terms, keyword_descriptions)]),
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return result
        
        except Exception as e:
            LOG.error(f"Error in LangChain analysis: {e}")
            return KeywordAnalysis(
                matched_keywords=[],
                relevance_scores={},
                contexts={},
                semantic_matches=[]
            )
    
    def find_keyword_matches(self, text: str, keywords: List[Keyword]) -> Dict[str, KeywordMatch]:
        """Find all keyword matches using both direct and semantic matching.
        
        Combines traditional string matching with AI semantic analysis to identify
        keyword presence, even when exact terms aren't used.
        
        Args:
            text: Text to analyze for keyword matches
            keywords: List of keyword configurations to search for
            
        Returns:
            Dictionary mapping keyword terms to their match details
        """
        processed_text = self.preprocess_text(text)
        
        langchain_analysis = self.analyze_with_langchain(text, keywords)
        
        matches = {}
        
        for keyword in keywords:
            keyword_term = keyword.term.lower()
            
            direct_occurrences = processed_text.count(keyword_term)
            pattern = r'\b' + re.escape(keyword_term) + r'\b'
            regex_matches = len(re.findall(pattern, processed_text))
            
            total_occurrences = max(direct_occurrences, regex_matches)
            
            relevance_score = langchain_analysis.relevance_scores.get(keyword.term, 0.0)
            
            if keyword.term in langchain_analysis.matched_keywords or keyword.term in langchain_analysis.semantic_matches:
                if total_occurrences == 0 and relevance_score > 0.1:
                    total_occurrences = 1
            
            contexts = langchain_analysis.contexts.get(keyword.term, [])
            if not contexts and total_occurrences > 0:
                contexts = self.extract_keyword_contexts(processed_text, keyword_term)
            
            if total_occurrences > 0 or relevance_score > 0.1:
                matches[keyword_term] = KeywordMatch(
                    keyword=keyword,
                    occurrences=int(total_occurrences),
                    contexts=contexts,
                    relevance_score=relevance_score
                )
        
        return matches
    
    def calculate_score(self, text: str, topic: Topic) -> ScoringResult:
        """Calculate comprehensive relevance score for text against a topic.
        
        Evaluates text coverage using weighted keyword matching, semantic analysis,
        and various scoring bonuses for comprehensiveness and length.
        
        Args:
            text: Text to score
            topic: Topic configuration with keywords and weights
            
        Returns:
            ScoringResult with total score and detailed breakdown
        """
        matches = self.find_keyword_matches(text, topic.keywords)
        
        total_possible_weight = sum(kw.weight for kw in topic.keywords)
        achieved_weight = 0.0
        detailed_breakdown = {}
        
        for keyword_term, match in matches.items():
            keyword_weight = match.keyword.weight
            
            occurrence_score = min(1.0, match.occurrences * 0.3)
            relevance_bonus = match.relevance_score
            
            keyword_contribution = keyword_weight * (occurrence_score + relevance_bonus) / 2
            achieved_weight += keyword_contribution
            
            detailed_breakdown[keyword_term] = {
                'weight': keyword_weight,
                'occurrences': match.occurrences,
                'relevance': match.relevance_score,
                'contribution': keyword_contribution
            }
        
        base_score = (achieved_weight / total_possible_weight) * 100 if total_possible_weight > 0 else 0
        
        coverage_bonus = (len(matches) / len(topic.keywords)) * 10
        
        length_bonus = min(5, len(text.split()) / 20)
        
        total_score = min(100, base_score + coverage_bonus + length_bonus)
        
        coverage_percentage = (len(matches) / len(topic.keywords)) * 100 if topic.keywords else 0
        
        return ScoringResult(
            total_score=total_score,
            keyword_matches=matches,
            coverage_percentage=coverage_percentage,
            detailed_breakdown=detailed_breakdown
        )
    
    def analyze_conversation(self, conversation_turns: List[str], topic: Topic) -> ScoringResult:
        """Analyze a multi-turn conversation for topic coverage.
        
        Args:
            conversation_turns: List of conversation messages
            topic: Topic configuration to analyze against
            
        Returns:
            ScoringResult for the combined conversation text
        """
        full_text = ' '.join(conversation_turns)
        return self.calculate_score(full_text, topic)
    
    def get_missing_keywords(self, matches: Dict[str, KeywordMatch], topic: Topic) -> List[Keyword]:
        """Identify keywords from the topic that weren't matched.
        
        Args:
            matches: Dictionary of successfully matched keywords
            topic: Original topic configuration
            
        Returns:
            List of keywords that weren't found in the text
        """
        matched_terms = set(matches.keys())
        all_terms = {kw.term.lower() for kw in topic.keywords}
        missing_terms = all_terms - matched_terms
        
        return [kw for kw in topic.keywords if kw.term.lower() in missing_terms]
    
    def generate_improvement_suggestions(self, scoring_result: ScoringResult, topic: Topic) -> List[str]:
        """Generate actionable suggestions for improving topic coverage.
        
        Analyzes scoring results to provide specific recommendations for
        better covering the topic in future conversation turns.
        
        Args:
            scoring_result: Results from previous analysis
            topic: Topic configuration being discussed
            
        Returns:
            List of human-readable improvement suggestions
        """
        suggestions = []
        
        missing_keywords = self.get_missing_keywords(scoring_result.keyword_matches, topic)
        
        if missing_keywords:
            high_priority = [kw for kw in missing_keywords if kw.weight > 1.1]
            if high_priority:
                suggestions.append(
                    f"Consider discussing these important aspects: {', '.join([kw.term for kw in high_priority[:3]])}"
                )
        
        low_relevance_matches = [
            match for match in scoring_result.keyword_matches.values() 
            if match.relevance_score < 0.3
        ]
        
        if low_relevance_matches:
            suggestions.append(
                "Try to provide more detailed explanations and context for the topics you mention"
            )
        
        if scoring_result.coverage_percentage < 50:
            suggestions.append(
                f"You've covered {scoring_result.coverage_percentage:.1f}% of the key areas. Try to explore more aspects of {topic.name}"
            )
        return suggestions