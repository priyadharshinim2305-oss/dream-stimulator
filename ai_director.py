# ai_director.py

import random
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

class ChoiceType(Enum):
    NEUTRAL = 0
    CONFRONT = 1
    FLEE = 2
    INVESTIGATE = 3
    IGNORE = 4

@dataclass
class DreamChoice:
    text: str
    choice_type: ChoiceType
    fear_impact: float
    tension_impact: float
    psychological_tags: List[str] = field(default_factory=list)
    leads_to_symbol: Optional[str] = None
    deepens_dream: bool = False

@dataclass
class DreamSceneData:
    narrative: str
    atmosphere: str
    imagery: List[str]
    choices: List[DreamChoice]
    hidden_meaning: str = ""
    recurring_symbols: List[str] = field(default_factory=list)


class AIDirector:
    """
    The AI Director manages the psychological evolution of dreams.
    It tracks patterns, adapts content, and creates increasingly personal experiences.
    """
    
    # Symbol pools by category
    SYMBOLS = {
        "fear": [
            "a faceless figure", "endless corridors", "teeth falling out",
            "being chased", "drowning", "falling", "paralysis",
            "the shadow self", "locked doors", "the void",
            "distorted mirrors", "time loops", "being watched"
        ],
        "memory": [
            "childhood home", "old photographs", "familiar strangers",
            "forgotten rooms", "school hallways", "family dinner table",
            "a ticking clock", "handwritten letters", "old toys"
        ],
        "desire": [
            "flying", "a golden door", "a garden", "reunion",
            "a warm light", "embracing someone", "finding something lost",
            "speaking truth", "freedom", "transformation"
        ],
        "anxiety": [
            "unprepared for an exam", "naked in public", "missing a flight",
            "lost in a city", "phone won't work", "can't speak",
            "running in slow motion", "late for something important"
        ],
        "existential": [
            "infinite stairs", "the edge of the world", "a door to nowhere",
            "meeting yourself", "the last day", "everyone disappeared",
            "reality fragmenting", "waking up within a dream"
        ]
    }
    
    # Atmosphere descriptions
    ATMOSPHERE_DETAILS = {
        "peaceful": {
            "lighting": ["soft golden", "warm afternoon", "gentle moonlight"],
            "sounds": ["distant music", "gentle breeze", "calm water"],
            "textures": ["soft grass", "warm wood", "smooth stone"]
        },
        "unsettling": {
            "lighting": ["flickering", "too bright", "wrong shadows"],
            "sounds": ["whispers", "distant footsteps", "static"],
            "textures": ["sticky", "too smooth", "slightly wet"]
        },
        "tense": {
            "lighting": ["harsh contrast", "strobing", "red-tinged"],
            "sounds": ["heartbeat", "breathing", "creaking"],
            "textures": ["cold metal", "rough concrete", "thorns"]
        },
        "terrifying": {
            "lighting": ["absolute darkness", "sickly green", "impossible angles"],
            "sounds": ["screaming silence", "your own voice", "scratching"],
            "textures": ["flesh-like", "decay", "sharp edges everywhere"]
        },
        "surreal": {
            "lighting": ["colors that don't exist", "liquid light", "geometric"],
            "sounds": ["backwards music", "colors as sound", "time itself"],
            "textures": ["shifting", "alive", "mathematical"]
        },
        "void": {
            "lighting": ["absence", "the memory of light", "negative space"],
            "sounds": ["the sound of forgetting", "entropy", "silence that screams"],
            "textures": ["nothing", "everything", "the space between atoms"]
        }
    }
    
    # Narrative templates by depth level
    DEPTH_NARRATIVES = {
        1: [  # Surface Dreams
            "You find yourself in {location}. The air feels {quality}. {symbol} catches your attention.",
            "{location} stretches before you. Something about it feels {quality}. You notice {symbol}.",
            "The dream begins in {location}. Everything seems {quality} at first. Then you see {symbol}."
        ],
        2: [  # Subconscious Echoes
            "This place... you've been here before, haven't you? {location} shifts around you, {quality}. {symbol} appears, and with it, a feeling you can't name.",
            "Memory and dream blur. {location} contains echoes of somewhere real. The {quality} atmosphere makes {symbol} feel significant.",
            "You recognize {location} but it's wrong somehow—{quality}. {symbol} triggers something deep."
        ],
        3: [  # Deep Memory
            "The dream pulls you deeper. {location} isn't just a place—it's a feeling, {quality} and raw. {symbol} speaks to something you've buried.",
            "Here, in {location}, the dream knows things about you. The {quality} weight of {symbol} presses on your chest.",
            "{location} transforms as you watch, becoming more {quality}. {symbol} has always been waiting here."
        ],
        4: [  # Primal Fears
            "You've gone too deep. {location} doesn't exist, yet here it is—{quality} beyond words. {symbol} isn't a symbol anymore. It's REAL.",
            "This is where dreams become truths. {location} is {quality}, ancient, fundamental. {symbol} is the shape of your oldest fear.",
            "The architecture of your psyche reveals itself: {location}, {quality} and absolute. {symbol} has your face."
        ],
        5: [  # The Void
            "Beyond dreaming. Beyond memory. {location} IS you—{quality}, infinite, terrifying. {symbol} asks the only question that matters.",
            "The void dreams you now. {location} and {symbol} are one—{quality}—and you finally understand why you've been running.",
            "Here at the bottom of yourself: {location}. {quality}. {symbol}. No more choices. Only truth."
        ]
    }
    
    # Location pools
    LOCATIONS = {
        "mundane": ["your childhood bedroom", "an office building", "a shopping mall", "your school", "a hospital waiting room"],
        "liminal": ["an empty train station", "a hotel hallway", "a parking structure at night", "an abandoned pool", "a closed airport"],
        "surreal": ["a house with infinite rooms", "a forest of hands", "a library of unwritten books", "stairs that go both up and down", "a museum of your memories"],
        "void": ["the space between thoughts", "the moment before waking", "the shape of loss", "the color of forgetting", "the texture of time"]
    }

    def __init__(self, dream_engine):
        self.engine = dream_engine
        self.session_symbols = []
        self.recurring_elements = []
        self.psychological_profile = {}
    
    def initialize_session(self, user_profile: Optional[dict] = None):
        """Initialize a new dream session with user's psychological history."""
        self.session_symbols = []
        self.recurring_elements = []
        self.psychological_profile = user_profile or {
            "confrontation": 0.5,
            "avoidance": 0.5,
            "curiosity": 0.5,
            "denial": 0.5,
            "primary_fears": [],
            "recurring_symbols": []
        }
        
        # Seed recurring elements from past dreams
        if user_profile and user_profile.get("recurring_symbols"):
            self.recurring_elements = user_profile["recurring_symbols"][:5]
    
    def generate_scene(
        self,
        session_data: dict,
        scene_number: int,
        previous_choice: Optional[dict] = None
    ) -> DreamSceneData:
        """Generate a new dream scene based on current state."""
        
        fear_level = session_data.get("fear_level", 0)
        tension_level = session_data.get("tension_level", 0)
        dream_depth = session_data.get("dream_depth", 1)
        is_nightmare = session_data.get("is_nightmare", False)
        
        # Get atmosphere from C engine
        atmosphere = self.engine.select_atmosphere(
            fear_level, tension_level, dream_depth, is_nightmare
        )
        
        # Calculate distortion
        distortion = self.engine.calculate_distortion(
            fear_level, tension_level, dream_depth, scene_number
        )
        
        # Select appropriate elements
        location = self._select_location(dream_depth, distortion)
        symbols = self._select_symbols(dream_depth, fear_level, previous_choice)
        quality = self._select_quality(atmosphere)
        
        # Generate narrative
        narrative = self._compose_narrative(
            dream_depth, location, symbols, quality, 
            atmosphere, distortion, previous_choice
        )
        
        # Generate choices
        choices = self._generate_choices(
            dream_depth, atmosphere, fear_level, 
            tension_level, symbols, is_nightmare
        )
        
        # Imagery for visual rendering
        imagery = self._generate_imagery(atmosphere, symbols, distortion)
        
        # Track symbols for this session
        for symbol in symbols:
            if symbol not in self.session_symbols:
                self.session_symbols.append(symbol)
        
        return DreamSceneData(
            narrative=narrative,
            atmosphere=atmosphere,
            imagery=imagery,
            choices=choices,
            hidden_meaning=self._generate_hidden_meaning(symbols, dream_depth),
            recurring_symbols=[s for s in symbols if s in self.recurring_elements]
        )
    
    def _select_location(self, depth: int, distortion: float) -> str:
        """Select appropriate location based on dream depth."""
        if depth <= 1:
            pool = self.LOCATIONS["mundane"] + self.LOCATIONS["liminal"]
        elif depth == 2:
            pool = self.LOCATIONS["liminal"] + self.LOCATIONS["surreal"][:2]
        elif depth == 3:
            pool = self.LOCATIONS["liminal"][-2:] + self.LOCATIONS["surreal"]
        elif depth == 4:
            pool = self.LOCATIONS["surreal"] + self.LOCATIONS["void"][:2]
        else:
            pool = self.LOCATIONS["void"]
        
        # Higher distortion = more surreal locations
        if distortion > 0.5 and depth < 5:
            pool = pool + self.LOCATIONS["surreal"]
        
        return random.choice(pool)
    
    def _select_symbols(
        self, 
        depth: int, 
        fear_level: float, 
        previous_choice: Optional[dict]
    ) -> List[str]:
        """Select psychological symbols for the scene."""
        symbols = []
        
        # Determine symbol categories based on state
        if fear_level > 6:
            primary_category = "fear"
        elif depth >= 4:
            primary_category = "existential"
        elif fear_level > 3:
            primary_category = "anxiety"
        else:
            primary_category = random.choice(["memory", "desire", "anxiety"])
        
        # Add primary symbol
        symbols.append(random.choice(self.SYMBOLS[primary_category]))
        
        # Chance for recurring symbol
        if self.recurring_elements and random.random() < 0.3:
            symbols.append(random.choice(self.recurring_elements))
        
        # Previous choice might trigger specific symbols
        if previous_choice:
            choice_type = previous_choice.get("choice_type", 0)
            if choice_type == 2:  # Fled - chase symbol
                symbols.append("something following you")
            elif choice_type == 4:  # Ignored - return of ignored
                symbols.append("the thing you tried to forget")
        
        return symbols[:3]  # Limit to 3 symbols per scene
    
    def _select_quality(self, atmosphere: str) -> str:
        """Select descriptive quality based on atmosphere."""
        if atmosphere in self.ATMOSPHERE_DETAILS:
            details = self.ATMOSPHERE_DETAILS[atmosphere]
            qualities = []
            if "lighting" in details:
                qualities.append(random.choice(details["lighting"]))
            if "textures" in details:
                qualities.append(random.choice(details["textures"]))
            return " and ".join(qualities)
        return "strange"
    
    def _compose_narrative(
        self,
        depth: int,
        location: str,
        symbols: List[str],
        quality: str,
        atmosphere: str,
        distortion: float,
        previous_choice: Optional[dict]
    ) -> str:
        """Compose the scene narrative."""
        
        # Get template
        templates = self.DEPTH_NARRATIVES.get(depth, self.DEPTH_NARRATIVES[1])
        template = random.choice(templates)
        
        # Format template
        narrative = template.format(
            location=location,
            quality=quality,
            symbol=symbols[0] if symbols else "something"
        )
        
        # Add continuation based on previous choice
        if previous_choice:
            choice_type = previous_choice.get("choice_type", 0)
            continuations = {
                1: "Your confrontation echoes here. ",
                2: "You thought you escaped, but the dream remembers. ",
                3: "What you found follows you deeper. ",
                4: "What you ignored grows stronger. "
            }
            if choice_type in continuations:
                narrative = continuations[choice_type] + narrative
        
        # Add distortion effects
        if distortion > 0.6:
            distortion_effects = [
                " The edges of everything blur and shift.",
                " Reality here is thin, unstable.",
                " You can feel the dream watching you.",
                " Time moves strangely—forward and backward at once."
            ]
            narrative += random.choice(distortion_effects)
        
        # Add extra symbols
        if len(symbols) > 1:
            narrative += f" In the periphery, you sense {symbols[1]}."
        
        # Atmosphere-specific additions
        if atmosphere == "terrifying":
            narrative += " Every instinct screams danger."
        elif atmosphere == "void":
            narrative += " This place exists beyond the dream itself."
        
        return narrative
    
    def _generate_choices(
        self,
        depth: int,
        atmosphere: str,
        fear_level: float,
        tension_level: float,
        symbols: List[str],
        is_nightmare: bool
    ) -> List[DreamChoice]:
        """Generate contextual choices for the player."""
        
        choices = []
        
        # Base choice templates
        choice_templates = {
            ChoiceType.CONFRONT: [
                "Face whatever waits ahead",
                "Turn toward the {symbol}",
                "Demand answers from the dream",
                "Stop running and stand your ground",
                "Reach out and touch it"
            ],
            ChoiceType.FLEE: [
                "Run—now, before it's too late",
                "Find a way out, any way",
                "Wake up—you need to wake up",
                "Back away slowly",
                "Close your eyes and wish it away"
            ],
            ChoiceType.INVESTIGATE: [
                "Look closer at {symbol}",
                "Search for meaning in this place",
                "Follow the thread deeper",
                "Listen—there's something here",
                "Open the door you weren't supposed to find"
            ],
            ChoiceType.IGNORE: [
                "Pretend none of this is real",
                "Focus on something else entirely",
                "It's just a dream—keep walking",
                "Refuse to engage",
                "Turn your back on {symbol}"
            ]
        }
        
        # Calculate psychological impact
        base_fear_impact = 0.1 + depth * 0.1
        
        # Always include at least 3 choices
        for choice_type in [ChoiceType.CONFRONT, ChoiceType.FLEE, ChoiceType.INVESTIGATE]:
            template = random.choice(choice_templates[choice_type])
            text = template.format(symbol=symbols[0] if symbols else "it")
            
            # Calculate impacts
            if choice_type == ChoiceType.CONFRONT:
                fear_impact = -base_fear_impact * 0.5
                tension_impact = 0.3
                tags = ["brave", "direct"]
            elif choice_type == ChoiceType.FLEE:
                fear_impact = base_fear_impact * 1.5
                tension_impact = -0.2
                tags = ["avoidant", "survival"]
            else:  # INVESTIGATE
                fear_impact = base_fear_impact
                tension_impact = 0.1
                tags = ["curious", "seeking"]
            
            choices.append(DreamChoice(
                text=text,
                choice_type=choice_type,
                fear_impact=fear_impact,
                tension_impact=tension_impact,
                psychological_tags=tags,
                deepens_dream=(choice_type == ChoiceType.INVESTIGATE and random.random() < 0.3)
            ))
        
        # Fourth choice varies by state
        if is_nightmare or fear_level > 7:
            # Desperate choice
            choices.append(DreamChoice(
                text="Scream until you wake",
                choice_type=ChoiceType.FLEE,
                fear_impact=0.5,
                tension_impact=-0.5,
                psychological_tags=["desperate", "breaking"]
            ))
        elif depth >= 4:
            # Acceptance choice at deep levels
            choices.append(DreamChoice(
                text="Let the dream consume you completely",
                choice_type=ChoiceType.NEUTRAL,
                fear_impact=-0.3,
                tension_impact=-0.3,
                psychological_tags=["surrender", "transcendent"],
                deepens_dream=True
            ))
        else:
            # Standard ignore choice
            template = random.choice(choice_templates[ChoiceType.IGNORE])
            choices.append(DreamChoice(
                text=template.format(symbol=symbols[0] if symbols else "it"),
                choice_type=ChoiceType.IGNORE,
                fear_impact=base_fear_impact * 0.8,
                tension_impact=0.2,
                psychological_tags=["denial", "avoidant"]
            ))
        
        random.shuffle(choices)
        return choices
    
    def _generate_imagery(
        self, 
        atmosphere: str, 
        symbols: List[str], 
        distortion: float
    ) -> List[str]:
        """Generate visual imagery descriptions for rendering."""
        imagery = []
        
        if atmosphere in self.ATMOSPHERE_DETAILS:
            details = self.ATMOSPHERE_DETAILS[atmosphere]
            imagery.append(f"Lighting: {random.choice(details.get('lighting', ['dim']))}")
            imagery.append(f"Sound: {random.choice(details.get('sounds', ['silence']))}")
        
        for symbol in symbols[:2]:
            imagery.append(f"Symbol: {symbol}")
        
        imagery.append(f"Distortion level: {distortion:.2f}")
        
        return imagery
    
    def _generate_hidden_meaning(self, symbols: List[str], depth: int) -> str:
        """Generate psychological interpretation for analytics."""
        meanings = {
            "a faceless figure": "fear of loss of identity",
            "endless corridors": "feeling trapped in routines",
            "teeth falling out": "anxiety about appearance or communication",
            "being chased": "avoiding confrontation with problems",
            "drowning": "overwhelmed by emotions",
            "falling": "loss of control",
            "childhood home": "nostalgia or unresolved past",
            "old photographs": "dwelling on memory",
            "familiar strangers": "disconnection from relationships",
            "flying": "desire for freedom",
            "infinite stairs": "endless striving without arrival",
            "the void": "existential questioning"
        }
        
        interpretations = []
        for symbol in symbols:
            if symbol in meanings:
                interpretations.append(meanings[symbol])
        
        depth_meaning = {
            1: "Surface-level processing",
            2: "Subconscious emergence",
            3: "Deep memory integration",
            4: "Core fear confrontation",
            5: "Ego dissolution"
        }
        
        interpretations.append(depth_meaning.get(depth, "Unknown depth"))
        
        return "; ".join(interpretations)
    
    def process_choice(
        self,
        choice: DreamChoice,
        response_time_ms: int,
        session_data: dict
    ) -> Tuple[dict, dict]:
        """
        Process a player's choice and return updated state and psychological analysis.
        """
        fear_level = session_data.get("fear_level", 0)
        tension_level = session_data.get("tension_level", 0)
        dream_depth = session_data.get("dream_depth", 1)
        
        # Get profile values
        profile = self.psychological_profile
        
        # Calculate fear change using C engine
        response_time_seconds = response_time_ms / 1000.0
        fear_delta = self.engine.calculate_fear_escalation(
            fear_level=fear_level,
            tension_level=tension_level,
            anxiety_baseline=profile.get("anxiety_baseline", 0.5),
            confrontation_tendency=profile.get("confrontation", 0.5),
            avoidance_tendency=profile.get("avoidance", 0.5),
            dream_depth=dream_depth,
            choice_type=choice.choice_type.value,
            response_time=response_time_seconds
        )
        
        # Add choice-specific impacts
        fear_delta += choice.fear_impact
        tension_delta = choice.tension_impact
        
        # Update state
        new_fear = max(0, min(10, fear_level + fear_delta))
        new_tension = max(0, min(10, tension_level + tension_delta))
        
        # Check for nightmare trigger
        is_nightmare = session_data.get("is_nightmare", False)
        if not is_nightmare:
            is_nightmare = self.engine.should_trigger_nightmare(
                new_fear,
                profile.get("avoidance", 0.5),
                dream_depth
            )
        
        # Deepen dream?
        new_depth = dream_depth
        if choice.deepens_dream and dream_depth < 5:
            new_depth = dream_depth + 1
        
        # Psychological analysis
        analysis = {
            "choice_type": choice.choice_type.name,
            "response_time_ms": response_time_ms,
            "tags": choice.psychological_tags,
            "fear_change": fear_delta,
            "tension_change": tension_delta,
            "depth_change": new_depth - dream_depth,
            "panic_response": response_time_ms < 2000,
            "hesitation": response_time_ms > 10000
        }
        
        # Update running profile
        if choice.choice_type == ChoiceType.CONFRONT:
            self.psychological_profile["confrontation"] = min(1.0, 
                profile.get("confrontation", 0.5) + 0.05)
        elif choice.choice_type == ChoiceType.FLEE:
            self.psychological_profile["avoidance"] = min(1.0,
                profile.get("avoidance", 0.5) + 0.05)
        
        updated_state = {
            "fear_level": new_fear,
            "tension_level": new_tension,
            "dream_depth": new_depth,
            "is_nightmare": is_nightmare
        }
        
        return updated_state, analysis
    
    def generate_ending(self, session_data: dict, total_scenes: int) -> str:
        """Generate dream ending based on session history."""
        fear_level = session_data.get("fear_level", 0)
        dream_depth = session_data.get("dream_depth", 1)
        is_nightmare = session_data.get("is_nightmare", False)
        
        if is_nightmare:
            endings = [
                "You wake up screaming, but the silence that follows is worse. Something came back with you.",
                "The dream releases you, but reluctantly. In the darkness of your room, you're not sure you're really awake.",
                "You surface gasping. The fear fades slowly, but the images remain, burned into your mind.",
                "Waking feels like drowning in reverse. For a moment, you forgot which reality was real."
            ]
        elif dream_depth >= 4:
            endings = [
                "You emerge from depths you didn't know you had. Something has changed—you can feel it.",
                "The dream lets you go, but leaves a mark. You've seen what lives beneath your thoughts.",
                "Rising through layers of consciousness, you carry a piece of the void with you.",
                "You wake different. The dream showed you truth, and truth cannot be unseen."
            ]
        elif fear_level < 3:
            endings = [
                "The dream fades gently, leaving only warmth and a sense of peace.",
                "You wake slowly, naturally, as the dream dissolves like morning mist.",
                "Reality returns softly. Something in the dream offered comfort.",
                "The transition to waking is smooth. This was one of the good ones."
            ]
        else:
            endings = [
                "You wake uncertain, the dream already fading to fragments.",
                "Morning pulls you back. The dream lingers at the edges—unsettling but unclear.",
                "You return to consciousness with unanswered questions.",
                "The dream ends mid-thought. You're left with feeling without memory."
            ]
        
        return random.choice(endings)
    
    def get_session_analysis(self, choices_history: List[dict]) -> dict:
        """Generate comprehensive psychological analysis of the session."""
        if not choices_history:
            return {"error": "No choices recorded"}
        
        choice_types = [c.get("choice_type", 0) for c in choices_history]
        response_times = [c.get("response_time", 5000) / 1000.0 for c in choices_history]
        
        patterns = self.engine.analyze_choice_patterns(choice_types, response_times)
        
        # Additional analysis
        panic_count = sum(1 for t in response_times if t < 2.0)
        hesitation_count = sum(1 for t in response_times if t > 10.0)
        
        avg_response_time = sum(response_times) / len(response_times)
        
        # Generate insights
        insights = []
        
        if patterns["avoidance"] > 0.5:
            insights.append("You tend to flee from dream challenges. This may reflect avoidance patterns in waking life.")
        
        if patterns["confrontation"] > 0.5:
            insights.append("You often choose to confront fears directly. This suggests resilience and willingness to face difficulties.")
        
        if patterns["curiosity"] > 0.4:
            insights.append("Your investigative choices show a drive to understand rather than simply react.")
        
        if patterns["denial"] > 0.3:
            insights.append("Frequent dismissal of dream elements may indicate discomfort with introspection.")
        
        if panic_count > len(response_times) * 0.3:
            insights.append("Quick, reactive choices suggest heightened anxiety states during dreams.")
        
        if hesitation_count > len(response_times) * 0.3:
            insights.append("Long deliberation times may indicate analysis paralysis or fear of consequences.")
        
        # Symbol analysis
        recurring = [s for s in self.session_symbols if self.session_symbols.count(s) > 1]
        
        return {
            "behavioral_patterns": patterns,
            "response_metrics": {
                "average_response_time_seconds": round(avg_response_time, 2),
                "panic_responses": panic_count,
                "hesitations": hesitation_count,
                "total_choices": len(choices_history)
            },
            "symbols_encountered": self.session_symbols,
            "recurring_symbols": recurring,
            "psychological_insights": insights,
            "session_profile": self.psychological_profile
        }
