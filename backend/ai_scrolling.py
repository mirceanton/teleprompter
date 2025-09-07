"""
AI Scrolling Service for Remote Teleprompter
Provides speech-to-text functionality and intelligent scrolling based on presenter's speech.
"""

import asyncio
import json
import logging
import difflib
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import io
import wave

# Speech recognition imports (optional dependencies)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None
    print("Warning: OpenAI Whisper not available. AI scrolling will use mock functionality for development.")

logger = logging.getLogger(__name__)

@dataclass
class AIScrollingConfig:
    """Configuration for AI scrolling behavior"""
    enabled: bool = False
    look_ahead_chars: int = 100
    look_behind_chars: int = 50
    confidence_threshold: float = 0.7
    pause_threshold_seconds: float = 3.0
    scroll_speed_multiplier: float = 1.0
    audio_source: str = "controller"  # "controller" or "teleprompter"

class TextMatcher:
    """Handles text matching between spoken words and script content"""
    
    def __init__(self, script_content: str, config: AIScrollingConfig):
        self.script_content = script_content
        self.config = config
        self.current_position = 0
        self.words = self._extract_words(script_content)
        
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text for matching"""
        # Remove markdown formatting and normalize
        clean_text = re.sub(r'[#*_`]', '', text)
        words = re.findall(r'\b\w+\b', clean_text.lower())
        return words
    
    def find_best_match(self, spoken_text: str) -> Optional[Tuple[int, float]]:
        """Find the best match for spoken text in the script"""
        if not spoken_text.strip():
            return None
            
        spoken_words = self._extract_words(spoken_text)
        if not spoken_words:
            return None
        
        # Search within look-ahead/behind window
        start_idx = max(0, self.current_position - self.config.look_behind_chars)
        end_idx = min(len(self.words), self.current_position + self.config.look_ahead_chars)
        
        search_words = self.words[start_idx:end_idx]
        
        # Try to find the best matching sequence
        best_match_idx = None
        best_score = 0.0
        
        for i in range(len(search_words) - len(spoken_words) + 1):
            candidate = search_words[i:i + len(spoken_words)]
            score = self._calculate_similarity(spoken_words, candidate)
            
            if score > best_score and score >= self.config.confidence_threshold:
                best_score = score
                best_match_idx = start_idx + i
        
        if best_match_idx is not None:
            return best_match_idx, best_score
        
        return None
    
    def _calculate_similarity(self, words1: List[str], words2: List[str]) -> float:
        """Calculate similarity between two word sequences"""
        if not words1 or not words2:
            return 0.0
        
        # Use sequence matcher for similarity
        matcher = difflib.SequenceMatcher(None, words1, words2)
        return matcher.ratio()
    
    def update_position(self, new_position: int):
        """Update current reading position"""
        self.current_position = max(0, min(len(self.words) - 1, new_position))
    
    def get_character_position(self, word_position: int) -> int:
        """Convert word position to character position in original text"""
        if word_position >= len(self.words):
            return len(self.script_content)
        
        # Approximate character position based on word position
        # This is a simplified implementation
        words_so_far = self.words[:word_position]
        approx_chars = sum(len(word) + 1 for word in words_so_far)  # +1 for spaces
        return min(approx_chars, len(self.script_content))

class AIScrollingService:
    """Main AI scrolling service that coordinates speech recognition and scrolling"""
    
    def __init__(self):
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.active_sessions: Dict[str, Dict] = {}
        
    async def initialize(self):
        """Initialize the speech recognition model"""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available. AI scrolling will use mock functionality.")
            return True  # Return True for development/testing
        
        try:
            # Load a small Whisper model for real-time transcription
            self.model = await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                lambda: whisper.load_model("tiny")
            )
            logger.info("AI scrolling service initialized with Whisper model")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AI scrolling: {e}")
            return False
    
    def create_session(self, channel: str, script_content: str, config: AIScrollingConfig):
        """Create a new AI scrolling session for a channel"""
        # Allow creation even without Whisper for development/testing
        text_matcher = TextMatcher(script_content, config)
        
        self.active_sessions[channel] = {
            "config": config,
            "text_matcher": text_matcher,
            "last_speech_time": None,
            "is_paused": False,
            "current_scroll_position": 0
        }
        
        logger.info(f"Created AI scrolling session for channel: {channel}")
    
    def remove_session(self, channel: str):
        """Remove AI scrolling session for a channel"""
        if channel in self.active_sessions:
            del self.active_sessions[channel]
            logger.info(f"Removed AI scrolling session for channel: {channel}")
    
    async def process_audio_chunk(self, channel: str, audio_data: bytes) -> Optional[Dict]:
        """Process audio chunk and return scrolling commands if needed"""
        if channel not in self.active_sessions:
            return None
        
        session = self.active_sessions[channel]
        config = session["config"]
        
        if not config.enabled:
            return None
        
        try:
            # If Whisper is not available, use mock functionality for development
            if not WHISPER_AVAILABLE or not self.model:
                return self._mock_process_audio_chunk(session, audio_data)
            
            # Convert audio data to format expected by Whisper
            audio_array = self._convert_audio_data(audio_data)
            
            # Transcribe audio
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.model.transcribe(audio_array, language="en")
            )
            
            spoken_text = result["text"].strip()
            
            if spoken_text:
                logger.debug(f"Transcribed: {spoken_text}")
                
                # Find match in script
                text_matcher = session["text_matcher"]
                match_result = text_matcher.find_best_match(spoken_text)
                
                if match_result:
                    word_position, confidence = match_result
                    char_position = text_matcher.get_character_position(word_position)
                    
                    # Update position
                    text_matcher.update_position(word_position)
                    session["current_scroll_position"] = char_position
                    session["last_speech_time"] = asyncio.get_event_loop().time()
                    session["is_paused"] = False
                    
                    # Calculate scroll command
                    return {
                        "type": "ai_scroll_to_position",
                        "position": char_position,
                        "confidence": confidence,
                        "spoken_text": spoken_text
                    }
                else:
                    # No match found - might be off-script
                    logger.debug(f"No match found for: {spoken_text}")
                    
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio for channel {channel}: {e}")
            return None
    
    def _mock_process_audio_chunk(self, session: dict, audio_data: bytes) -> Optional[Dict]:
        """Mock audio processing for development when Whisper is not available"""
        # Simulate progressive scrolling for testing
        current_position = session.get("current_scroll_position", 0)
        new_position = current_position + 50  # Advance by 50 characters
        
        session["current_scroll_position"] = new_position
        session["last_speech_time"] = asyncio.get_event_loop().time()
        session["is_paused"] = False
        
        return {
            "type": "ai_scroll_to_position",
            "position": new_position,
            "confidence": 0.8,
            "spoken_text": "[Mock speech detection]"
        }
    
    def _convert_audio_data(self, audio_data: bytes) -> bytes:
        """Convert audio data to format for processing"""
        # For now, just return the audio data as-is
        # In a real implementation with Whisper, this would convert to the proper format
        return audio_data
    
    async def check_pause_detection(self, channel: str) -> Optional[Dict]:
        """Check if presenter has paused and should pause scrolling"""
        if channel not in self.active_sessions:
            return None
        
        session = self.active_sessions[channel]
        config = session["config"]
        
        if not config.enabled or session["is_paused"]:
            return None
        
        current_time = asyncio.get_event_loop().time()
        last_speech_time = session.get("last_speech_time")
        
        if (last_speech_time and 
            current_time - last_speech_time > config.pause_threshold_seconds):
            
            session["is_paused"] = True
            return {
                "type": "ai_pause_scrolling",
                "reason": "speech_pause_detected"
            }
        
        return None
    
    def update_config(self, channel: str, config: AIScrollingConfig):
        """Update configuration for a channel"""
        if channel in self.active_sessions:
            self.active_sessions[channel]["config"] = config
            self.active_sessions[channel]["text_matcher"].config = config
    
    def get_session_info(self, channel: str) -> Optional[Dict]:
        """Get information about AI scrolling session"""
        if channel not in self.active_sessions:
            return None
        
        session = self.active_sessions[channel]
        return {
            "enabled": session["config"].enabled,
            "current_position": session["current_scroll_position"],
            "is_paused": session["is_paused"],
            "audio_source": session["config"].audio_source
        }

    def is_available(self) -> bool:
        """Check if AI scrolling is available (for development, always return True)"""
        return True  # For development/testing purposes

# Global AI scrolling service instance
ai_scrolling_service = AIScrollingService()