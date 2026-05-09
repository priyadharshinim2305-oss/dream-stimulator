# dream_engine.py

import ctypes
import os
import platform
from typing import Tuple, List
import random

class DreamEngine:
    """Python wrapper for the C dream engine with fallback implementations."""
    
    def __init__(self):
        self.c_lib = None
        self._load_c_library()
    
    def _load_c_library(self):
        """Attempt to load the C library."""
        try:
            if platform.system() == 'Windows':
                lib_name = 'dream_engine.dll'
            elif platform.system() == 'Darwin':
                lib_name = 'dream_engine.dylib'
            else:
                lib_name = 'dream_engine.so'
            
            lib_path = os.path.join(os.path.dirname(__file__), lib_name)
            
            if os.path.exists(lib_path):
                self.c_lib = ctypes.CDLL(lib_path)
                self._setup_c_functions()
                print(f"Loaded C dream engine from {lib_path}")
            else:
                print("C library not found, using Python fallback")
        except Exception as e:
            print(f"Could not load C library: {e}, using Python fallback")
    
    def _setup_c_functions(self):
        """Set up C function signatures."""
        if not self.c_lib:
            return
        
        # c_calculate_fear_escalation
        self.c_lib.c_calculate_fear_escalation.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_float,
            ctypes.c_float, ctypes.c_float, ctypes.c_int,
            ctypes.c_int, ctypes.c_float
        ]
        self.c_lib.c_calculate_fear_escalation.restype = ctypes.c_float
        
        # c_calculate_distortion
        self.c_lib.c_calculate_distortion.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_int
        ]
        self.c_lib.c_calculate_distortion.restype = ctypes.c_float
        
        # c_should_nightmare
        self.c_lib.c_should_nightmare.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_int
        ]
        self.c_lib.c_should_nightmare.restype = ctypes.c_int
        
        # c_select_atmosphere
        self.c_lib.c_select_atmosphere.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_int, 
            ctypes.c_int, ctypes.c_int
        ]
        self.c_lib.c_select_atmosphere.restype = ctypes.c_int
    
    def calculate_fear_escalation(
        self,
        fear_level: float,
        tension_level: float,
        anxiety_baseline: float,
        confrontation_tendency: float,
        avoidance_tendency: float,
        dream_depth: int,
        choice_type: int,
        response_time: float
    ) -> float:
        """Calculate fear change based on choice."""
        if self.c_lib:
            return self.c_lib.c_calculate_fear_escalation(
                fear_level, tension_level, anxiety_baseline,
                confrontation_tendency, avoidance_tendency,
                dream_depth, choice_type, response_time
            )
        
        # Python fallback
        base_escalation = {
            0: 0.1,   # neutral
            1: -0.3,  # confront
            2: 0.4,   # flee
            3: 0.2,   # investigate
            4: 0.3    # ignore
        }.get(choice_type, 0.1)
        
        if response_time < 2.0:
            base_escalation *= 1.5
        
        depth_multiplier = 1.0 + (dream_depth - 1) * 0.25
        return base_escalation * depth_multiplier
    
    def calculate_distortion(
        self,
        fear_level: float,
        tension_level: float,
        dream_depth: int,
        scene_count: int
    ) -> float:
        """Calculate how distorted/surreal the dream should be."""
        if self.c_lib:
            return self.c_lib.c_calculate_distortion(
                fear_level, tension_level, dream_depth, scene_count
            )
        
        # Python fallback
        distortion = dream_depth * 0.15
        distortion += fear_level * 0.05
        distortion += scene_count * 0.02
        distortion += tension_level * 0.03
        return min(distortion, 1.0)
    
    def should_trigger_nightmare(
        self,
        fear_level: float,
        avoidance_tendency: float,
        dream_depth: int
    ) -> bool:
        """Determine if nightmare mode should activate."""
        seed = random.randint(0, 100000)
        
        if self.c_lib:
            return bool(self.c_lib.c_should_nightmare(
                fear_level, avoidance_tendency, dream_depth, seed
            ))
        
        # Python fallback
        threshold = 7.5 - avoidance_tendency * 2.0 - (dream_depth - 1) * 0.5
        random_factor = random.uniform(0, 2.0)
        return (fear_level + random_factor) >= threshold
    
    def select_atmosphere(
        self,
        fear_level: float,
        tension_level: float,
        dream_depth: int,
        is_nightmare: bool
    ) -> str:
        """Select dream atmosphere based on psychological state."""
        seed = random.randint(0, 100000)
        
        if self.c_lib:
            atmosphere_id = self.c_lib.c_select_atmosphere(
                fear_level, tension_level, dream_depth,
                1 if is_nightmare else 0, seed
            )
        else:
            # Python fallback
            roll = random.random()
            fear_norm = fear_level / 10.0
            tension_norm = tension_level / 10.0
            
            if is_nightmare:
                atmosphere_id = 3 if roll < 0.3 else (2 if roll < 0.6 else 4)
            elif dream_depth >= 4:
                atmosphere_id = 5 if roll < 0.4 else 4
            elif fear_norm > 0.7:
                atmosphere_id = 3
            elif fear_norm > 0.4 or tension_norm > 0.6:
                atmosphere_id = 2
            elif fear_norm > 0.2:
                atmosphere_id = 1
            else:
                atmosphere_id = 0 if roll < 0.7 else 4
        
        atmospheres = {
            0: "peaceful",
            1: "unsettling",
            2: "tense",
            3: "terrifying",
            4: "surreal",
            5: "void"
        }
        return atmospheres.get(atmosphere_id, "surreal")
    
    def analyze_choice_patterns(
        self,
        choices: List[int],
        response_times: List[float]
    ) -> dict:
        """Analyze player's choice patterns for psychological profiling."""
        if not choices:
            return {
                "confrontation": 0.0,
                "avoidance": 0.0,
                "curiosity": 0.0,
                "denial": 0.0
            }
        
        total = len(choices)
        confront = sum(1 for c in choices if c == 1)
        flee = sum(1 for c in choices if c == 2)
        investigate = sum(1 for c in choices if c == 3)
        ignore = sum(1 for c in choices if c == 4)
        
        confrontation = confront / total
        avoidance = flee / total
        curiosity = investigate / total
        denial = ignore / total
        
        # Adjust based on response times
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time < 3.0:
                confrontation *= 1.2
                avoidance *= 1.2
            elif avg_time > 8.0:
                curiosity *= 1.3
        
        return {
            "confrontation": min(confrontation, 1.0),
            "avoidance": min(avoidance, 1.0),
            "curiosity": min(curiosity, 1.0),
            "denial": min(denial, 1.0)
        }


# Global instance
dream_engine = DreamEngine()
