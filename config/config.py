from dataclasses import dataclass
from typing import Dict, List
import random

@dataclass
class Keyword:
    """Represents a keyword used for conversation analysis.
    
    Attributes:
        term: The keyword or phrase to match
        description: Explanation of the keyword's relevance
        weight: Importance multiplier for scoring (default 1.0)
    """
    term: str
    description: str
    weight: float = 1.0

@dataclass
class Topic:
    """Represents a conversation topic with associated keywords.
    
    Attributes:
        name: Display name of the topic
        description: Brief explanation of what the topic covers
        keywords: List of relevant keywords for analysis
        introduction: Opening message to start conversations about this topic
    """
    name: str
    description: str
    keywords: List[Keyword]
    introduction: str

TOPICS_CONFIG: Dict[str, Topic] = {
    "weather": Topic(
        name="Weather",
        description="Understanding weather patterns and atmospheric conditions",
        keywords=[
            Keyword("temperature", "Driven by solar radiation, altitude, and latitude", 1.0),
            Keyword("humidity", "Amount of moisture in the air affecting comfort and precipitation", 1.0),
            Keyword("air pressure", "Influences wind and storm systems", 1.0),
            Keyword("wind patterns", "Caused by pressure differences and Earth's rotation", 1.0),
            Keyword("precipitation", "Rain, snow, sleet, or hail depending on atmospheric conditions", 1.0),
        ],
        introduction="Hey! I've heard that you have some interesting insights about weather patterns. Could you tell me more? What do you think has the biggest influence on weather?"
    ),
    
    "software_performance": Topic(
        name="Software Application Performance",
        description="Factors affecting software application efficiency and speed",
        keywords=[
            Keyword("algorithm efficiency", "Complexity and optimization of code logic", 1.0),
            Keyword("hardware resources", "CPU speed, memory capacity, and storage performance", 1.0),
            Keyword("network latency", "Especially for distributed or cloud-based apps", 1.0),
            Keyword("bandwidth", "Especially for distributed or cloud-based apps", 1.0),
            Keyword("concurrency", "Threading, async processing, and scaling ability", 1.0),
            Keyword("load handling", "Threading, async processing, and scaling ability", 1.0),
            Keyword("database query optimization", "Indexing, caching, and reducing I/O bottlenecks", 1.0),
        ],
        introduction="Hey! I've heard that you have some interesting insights about software application performance. Could you tell me more? What do you think has the biggest influence on how fast applications run?"
    ),
    
    "road_traffic": Topic(
        name="Road Traffic",
        description="Factors affecting traffic flow and road congestion",
        keywords=[
            Keyword("road infrastructure", "Quality, layout, and capacity of roads", 1.0),
            Keyword("traffic volume", "Number of vehicles and peak-hour surges", 1.0),
            Keyword("traffic signals", "Synchronization, signage, and smart systems", 1.0),
            Keyword("traffic control", "Synchronization, signage, and smart systems", 1.0),
            Keyword("accidents", "Unexpected disruptions reducing flow", 1.0),
            Keyword("roadworks", "Unexpected disruptions reducing flow", 1.0),
            Keyword("weather conditions", "Rain, snow, and fog affecting speed and safety", 1.0),
        ],
        introduction="Hey! I've heard that you have some interesting insights about road traffic and what causes congestion. Could you tell me more? What do you think has the biggest influence on traffic flow?"
    ),
    
    "job_interview": Topic(
        name="Successful Job Interview",
        description="Key factors for performing well in job interviews",
        keywords=[
            Keyword("preparation", "Understanding the company and role", 1.0),
            Keyword("research", "Understanding the company and role", 1.0),
            Keyword("communication skills", "Clear, concise, and confident speaking", 1.0),
            Keyword("body language", "Eye contact, posture, and facial expressions", 1.0),
            Keyword("relevant experience", "Direct alignment with job requirements", 1.0),
            Keyword("skills", "Direct alignment with job requirements", 1.0),
            Keyword("positive attitude", "Showing adaptability and enthusiasm", 1.0),
            Keyword("cultural fit", "Showing adaptability and enthusiasm", 1.0),
        ],
        introduction="Hey! I've heard that you have some interesting insights about what makes job interviews successful. Could you tell me more? What do you think has the biggest influence on interview success?"
    ),
    
    "volcanic_city_planning": Topic(
        name="City Planning in Volcanic Areas",
        description="Urban planning considerations for volcanic hazard zones",
        keywords=[
            Keyword("hazard mapping", "Identifying lava flow, ashfall, and lahar zones", 1.0),
            Keyword("lava flow", "Identifying lava flow, ashfall, and lahar zones", 1.0),
            Keyword("ashfall", "Identifying lava flow, ashfall, and lahar zones", 1.0),
            Keyword("lahar", "Identifying lava flow, ashfall, and lahar zones", 1.0),
            Keyword("evacuation routes", "Multiple, well-marked, and easily accessible", 1.0),
            Keyword("land use zoning", "Keeping high-risk zones free of permanent settlements", 1.0),
            Keyword("monitoring systems", "Seismic, thermal, and gas detection", 1.0),
            Keyword("early warning systems", "Seismic, thermal, and gas detection", 1.0),
            Keyword("emergency infrastructure", "Shelters, supply depots, and medical facilities", 1.0),
        ],
        introduction="Hey! I've heard that you have some interesting insights about city planning in volcanic areas. Could you tell me more? What do you think has the biggest influence on safe urban development near volcanoes?"
    )
}

def get_random_topic() -> Topic:
    """Select a random topic from the available configurations.
    
    Returns:
        Randomly selected Topic instance
    """
    return random.choice(list(TOPICS_CONFIG.values()))
