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
    """keyword match result."""
    keyword: Keyword
    found: bool
    score: float

@dataclass
class ScoringResult:
    """scoring result."""
    total_score: float
    keyword_matches: Dict[str, KeywordMatch]
    keywords_found: int
    total_keywords: int

class KeywordAnalysis(BaseModel):
    """LangChain analysis output"""
    matched_keywords: List[str] = Field(description="List of keywords found in the text")
    relevance_scores: Dict[str, float] = Field(description="Relevance score for each keyword (0.0-1.0)")

class KeywordAnalyzer:
    """keyword analyzer with basic AI assistance."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.llm = ChatOpenAI(model=get_conf('MODEL_NAME'), api_key=get_conf('OPENAI_API_KEY'), temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=KeywordAnalysis)
        self.setup_prompt_template()
    
    def setup_prompt_template(self):
        """prompt for keyword analysis."""
        template = """
        Find these keywords in the text: {keywords}
        
        Text: {text}
        
        For each keyword, give a score from 0.0 to 1.0 based on how well it's discussed.
        
        {format_instructions}
        """
        
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm | self.parser
    
    def check_keyword_in_text(self, text: str, keyword: str) -> bool:
        """keyword check."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        return keyword_lower in text_lower
    
    def analyze_with_langchain(self, text: str, keywords: List[Keyword]) -> KeywordAnalysis:
        """AI analysis."""
        try:
            keyword_terms = [kw.term for kw in keywords]
            
            result = self.chain.invoke({
                "text": text,
                "keywords": ", ".join(keyword_terms),
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return result
        
        except Exception as e:
            LOG.error(f"AI analysis error: {e}")
            return KeywordAnalysis(
                matched_keywords=[],
                relevance_scores={}
            )
    
    def find_keyword_matches(self, text: str, keywords: List[Keyword]) -> Dict[str, KeywordMatch]:
        """Find keyword matches using text search and AI scoring."""
        
        ai_analysis = self.analyze_with_langchain(text, keywords)
        matches = {}
        
        for keyword in keywords:
            # text search
            found = self.check_keyword_in_text(text, keyword.term)
            
            # Get AI score
            ai_score = ai_analysis.relevance_scores.get(keyword.term, 0.0)
            
            # If AI found it but text search didn't, still count it
            if keyword.term in ai_analysis.matched_keywords and not found:
                found = True
            
            # Calculate score
            if found:
                score = max(0.0, ai_score)
            else:
                score = ai_score  # Use AI score if not directly found
            
            if found or score > 0.1:
                matches[keyword.term] = KeywordMatch(
                    keyword=keyword,
                    found=found,
                    score=score
                )
        
        return matches
    
    def calculate_score(self, text: str, topic: Topic) -> ScoringResult:
        """scoring calculation."""
        
        matches = self.find_keyword_matches(text, topic.keywords)
        

        if matches:
            total_score = (sum(match.score for match in matches.values()) / len(topic.keywords)) * 100
        else:
            total_score = 0.0
        
        keywords_found = len(matches)
        total_keywords = len(topic.keywords)
        
        return ScoringResult(
            total_score=min(100, total_score),
            keyword_matches=matches,
            keywords_found=keywords_found,
            total_keywords=total_keywords
        )
    
    def analyze_conversation(self, conversation_turns: List[str], topic: Topic) -> ScoringResult:
        """Analyze conversation turns."""
        full_text = ' '.join(conversation_turns)
        return self.calculate_score(full_text, topic)
    
    def get_missing_keywords(self, scoring_result: ScoringResult, topic: Topic) -> List[str]:
        """Get keywords not found."""
        found_terms = set(scoring_result.keyword_matches.keys())
        all_terms = {kw.term for kw in topic.keywords}
        return list(all_terms - found_terms)
    
    def generate_improvement_suggestions(self, scoring_result: ScoringResult, topic: Topic) -> List[str]:
        """suggestions."""
        suggestions = []
        
        missing = self.get_missing_keywords(scoring_result, topic)
        if missing:
            suggestions.append(f"Try discussing: {', '.join(missing[:3])}")
        
        #if scoring_result.keywords_found < scoring_result.total_keywords / 2:
            #suggestions.append(f"Cover more topics - you've discussed {scoring_result.keywords_found} out of {scoring_result.total_keywords}")
        
        return suggestions