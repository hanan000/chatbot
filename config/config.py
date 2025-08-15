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
            Keyword("temperature", "Driven by solar radiation, altitude, and latitude", 1.2),
            Keyword("humidity", "Amount of moisture in the air affecting comfort and precipitation", 1.0),
            Keyword("air pressure", "Influences wind and storm systems", 1.1),
            Keyword("pressure", "Influences wind and storm systems", 1.1),
            Keyword("wind patterns", "Caused by pressure differences and Earth's rotation", 1.0),
            Keyword("wind", "Caused by pressure differences and Earth's rotation", 0.8),
            Keyword("precipitation", "Rain, snow, sleet, or hail depending on atmospheric conditions", 1.0),
            Keyword("rain", "Form of precipitation", 0.7),
            Keyword("snow", "Form of precipitation", 0.7),
            Keyword("storm", "Weather system with strong winds and precipitation", 0.9),
            Keyword("solar radiation", "Primary driver of temperature variations", 1.1),
            Keyword("altitude", "Height above sea level affecting temperature", 0.9),
            Keyword("latitude", "Distance from equator affecting temperature", 0.9),
        ],
        introduction="Hey! I've heard that you have some interesting insights about weather patterns. Could you tell me more? What do you think has the biggest influence on weather?"
    ),
    
    "software_performance": Topic(
        name="Software Application Performance",
        description="Factors affecting software application efficiency and speed",
        keywords=[
            Keyword("algorithm efficiency", "Complexity and optimization of code logic", 1.3),
            Keyword("algorithm", "Code logic and computational methods", 1.0),
            Keyword("complexity", "Computational complexity of algorithms", 1.1),
            Keyword("optimization", "Improving code performance", 1.2),
            Keyword("hardware resources", "CPU speed, memory capacity, and storage performance", 1.2),
            Keyword("cpu", "Central processing unit affecting performance", 1.0),
            Keyword("memory", "RAM capacity and usage", 1.0),
            Keyword("storage", "Disk I/O performance", 0.9),
            Keyword("network latency", "Delay in network communication", 1.1),
            Keyword("bandwidth", "Network data transfer capacity", 1.0),
            Keyword("concurrency", "Handling multiple operations simultaneously", 1.2),
            Keyword("threading", "Parallel execution of code", 1.0),
            Keyword("async", "Asynchronous processing", 1.1),
            Keyword("scaling", "Ability to handle increased load", 1.1),
            Keyword("database", "Data storage and retrieval system", 0.9),
            Keyword("query optimization", "Improving database query performance", 1.2),
            Keyword("indexing", "Database performance improvement technique", 1.0),
            Keyword("caching", "Storing frequently accessed data", 1.1),
        ],
        introduction="Hey! I've heard that you have some interesting insights about software application performance. Could you tell me more? What do you think has the biggest influence on how fast applications run?"
    ),
    
    "road_traffic": Topic(
        name="Road Traffic",
        description="Factors affecting traffic flow and road congestion",
        keywords=[
            Keyword("road infrastructure", "Quality, layout, and capacity of roads", 1.2),
            Keyword("infrastructure", "Road systems and facilities", 1.0),
            Keyword("road capacity", "Maximum traffic a road can handle", 1.1),
            Keyword("traffic volume", "Number of vehicles on roads", 1.2),
            Keyword("peak hours", "Times of highest traffic density", 1.0),
            Keyword("traffic signals", "Control systems for traffic flow", 1.1),
            Keyword("traffic control", "Management of vehicle movement", 1.0),
            Keyword("signage", "Road signs and markers", 0.8),
            Keyword("accidents", "Traffic incidents causing delays", 1.1),
            Keyword("roadworks", "Construction affecting traffic flow", 1.0),
            Keyword("construction", "Road maintenance and building", 0.9),
            Keyword("weather conditions", "Environmental factors affecting driving", 1.0),
            Keyword("congestion", "Traffic jams and slow movement", 1.1),
            Keyword("bottleneck", "Points where traffic flow is restricted", 1.0),
        ],
        introduction="Hey! I've heard that you have some interesting insights about road traffic and what causes congestion. Could you tell me more? What do you think has the biggest influence on traffic flow?"
    ),
    
    "job_interview": Topic(
        name="Successful Job Interview",
        description="Key factors for performing well in job interviews",
        keywords=[
            Keyword("preparation", "Getting ready for the interview", 1.3),
            Keyword("research", "Learning about the company and role", 1.2),
            Keyword("company research", "Understanding the employer", 1.1),
            Keyword("communication skills", "Clear and effective speaking", 1.2),
            Keyword("communication", "Verbal and non-verbal interaction", 1.0),
            Keyword("speaking", "Verbal communication ability", 0.9),
            Keyword("body language", "Non-verbal communication cues", 1.1),
            Keyword("eye contact", "Direct visual engagement", 0.9),
            Keyword("posture", "Physical positioning and stance", 0.8),
            Keyword("experience", "Relevant work background", 1.1),
            Keyword("skills", "Abilities relevant to the job", 1.0),
            Keyword("qualifications", "Education and certifications", 0.9),
            Keyword("attitude", "Positive mindset and demeanor", 1.0),
            Keyword("enthusiasm", "Showing interest and energy", 1.0),
            Keyword("cultural fit", "Matching company values", 1.0),
            Keyword("adaptability", "Flexibility and learning ability", 0.9),
        ],
        introduction="Hey! I've heard that you have some interesting insights about what makes job interviews successful. Could you tell me more? What do you think has the biggest influence on interview success?"
    ),
    
    "volcanic_city_planning": Topic(
        name="City Planning in Volcanic Areas",
        description="Urban planning considerations for volcanic hazard zones",
        keywords=[
            Keyword("hazard mapping", "Identifying volcanic risk zones", 1.3),
            Keyword("lava flow", "Path of molten rock", 1.1),
            Keyword("ashfall", "Volcanic ash distribution", 1.0),
            Keyword("lahar", "Volcanic mudflow hazard", 1.1),
            Keyword("evacuation routes", "Emergency exit pathways", 1.2),
            Keyword("evacuation", "Emergency population movement", 1.0),
            Keyword("emergency routes", "Critical escape paths", 1.1),
            Keyword("land use zoning", "Designated area restrictions", 1.2),
            Keyword("zoning", "Area usage regulations", 1.0),
            Keyword("settlement", "Residential development areas", 0.9),
            Keyword("monitoring systems", "Volcanic activity detection", 1.2),
            Keyword("early warning", "Advance hazard notification", 1.1),
            Keyword("seismic", "Earthquake monitoring related to volcanoes", 1.0),
            Keyword("thermal monitoring", "Heat detection systems", 0.9),
            Keyword("gas detection", "Volcanic gas monitoring", 0.9),
            Keyword("emergency infrastructure", "Disaster response facilities", 1.1),
            Keyword("shelters", "Emergency housing facilities", 1.0),
            Keyword("supply depots", "Emergency resource storage", 0.9),
            Keyword("medical facilities", "Healthcare emergency response", 1.0),
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
