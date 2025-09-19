"""
Room Management for Remote Teleprompter
Handles room creation, authentication, and participant management using Redis.
"""

import json
import secrets
import uuid
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from redis_manager import redis_manager

logger = logging.getLogger(__name__)

# Adjectives and animals for room name generation
ADJECTIVES = [
    "Amazing", "Brilliant", "Creative", "Dynamic", "Elegant", "Fantastic", "Gentle",
    "Happy", "Inspiring", "Joyful", "Kinetic", "Lively", "Magnificent", "Noble",
    "Optimistic", "Peaceful", "Quick", "Radiant", "Stellar", "Thoughtful",
    "Unique", "Vibrant", "Wonderful", "Exciting", "Young", "Zealous"
]

ANIMALS = [
    "Alpaca", "Bear", "Cat", "Dolphin", "Eagle", "Fox", "Giraffe", "Horse",
    "Iguana", "Jaguar", "Koala", "Lion", "Monkey", "Narwhal", "Owl", "Panda",
    "Quail", "Rabbit", "Swan", "Tiger", "Unicorn", "Viper", "Whale", "Xenops",
    "Yak", "Zebra"
]

@dataclass
class Participant:
    """Represents a participant in a room"""
    id: str
    role: str  # "controller" or "teleprompter"
    joined_at: str
    last_seen: str

@dataclass
class Room:
    """Represents a teleprompter room"""
    room_id: str
    room_secret: str
    room_name: str
    controller_id: Optional[str]
    participants: Dict[str, Participant]
    created_at: str
    last_activity: str

class RoomManager:
    """Manages rooms and participants in Redis"""
    
    def __init__(self):
        self.room_prefix = "teleprompter:room:"
        self.participant_prefix = "teleprompter:participant:"
        
    def _get_room_key(self, room_id: str) -> str:
        """Get Redis key for room data"""
        return f"{self.room_prefix}{room_id}"
    
    def _get_participant_key(self, participant_id: str) -> str:
        """Get Redis key for participant data"""
        return f"{self.participant_prefix}{participant_id}"
    
    def _generate_room_id(self) -> str:
        """Generate a unique room ID"""
        return f"room{uuid.uuid4().hex[:8]}"
    
    def _generate_room_secret(self) -> str:
        """Generate a 64-character room secret"""
        return secrets.token_urlsafe(48)  # 48 bytes = 64 URL-safe characters
    
    def _generate_room_name(self) -> str:
        """Generate a default room name"""
        adjective = random.choice(ADJECTIVES)
        animal = random.choice(ANIMALS)
        return f"{adjective} {animal} Room"
    
    def _generate_participant_id(self) -> str:
        """Generate a unique participant ID"""
        return f"participant_{uuid.uuid4().hex[:12]}"
    
    async def create_room(self, room_name: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Create a new room.
        
        Returns:
            Tuple of (room_id, room_secret, room_name)
        """
        try:
            room_id = self._generate_room_id()
            room_secret = self._generate_room_secret()
            if not room_name:
                room_name = self._generate_room_name()
            
            now = datetime.now(timezone.utc).isoformat()
            
            room = Room(
                room_id=room_id,
                room_secret=room_secret,
                room_name=room_name,
                controller_id=None,
                participants={},
                created_at=now,
                last_activity=now
            )
            
            # Store room in Redis
            room_key = self._get_room_key(room_id)
            await redis_manager.redis_client.set(
                room_key, 
                json.dumps(asdict(room)),
                ex=24 * 60 * 60  # Expire after 24 hours
            )
            
            logger.info(f"Created room {room_id} with name '{room_name}'")
            return room_id, room_secret, room_name
            
        except Exception as e:
            logger.error(f"Error creating room: {e}")
            raise
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get room data"""
        try:
            room_key = self._get_room_key(room_id)
            room_data = await redis_manager.redis_client.get(room_key)
            
            if not room_data:
                return None
            
            room_dict = json.loads(room_data)
            # Convert participants dict back to Participant objects
            participants = {}
            for pid, pdata in room_dict.get("participants", {}).items():
                participants[pid] = Participant(**pdata)
            
            room_dict["participants"] = participants
            return Room(**room_dict)
            
        except Exception as e:
            logger.error(f"Error getting room {room_id}: {e}")
            return None
    
    async def verify_room_access(self, room_id: str, room_secret: str) -> bool:
        """Verify that room exists and secret is correct"""
        try:
            room = await self.get_room(room_id)
            if not room:
                return False
            
            return room.room_secret == room_secret
            
        except Exception as e:
            logger.error(f"Error verifying access to room {room_id}: {e}")
            return False
    
    async def add_participant(self, room_id: str, role: str) -> Optional[str]:
        """
        Add a participant to a room.
        
        Args:
            room_id: The room ID
            role: "controller" or "teleprompter"
            
        Returns:
            participant_id if successful, None otherwise
        """
        try:
            room = await self.get_room(room_id)
            if not room:
                logger.warning(f"Attempt to add participant to non-existent room {room_id}")
                return None
            
            # Check if trying to add controller when one already exists
            if role == "controller" and room.controller_id:
                logger.warning(f"Attempt to add controller to room {room_id} that already has one")
                return None
            
            participant_id = self._generate_participant_id()
            now = datetime.now(timezone.utc).isoformat()
            
            participant = Participant(
                id=participant_id,
                role=role,
                joined_at=now,
                last_seen=now
            )
            
            # Add participant to room
            room.participants[participant_id] = participant
            room.last_activity = now
            
            # Set controller if this is a controller role
            if role == "controller":
                room.controller_id = participant_id
            
            # Update room in Redis
            room_key = self._get_room_key(room_id)
            await redis_manager.redis_client.set(
                room_key,
                json.dumps(asdict(room)),
                ex=24 * 60 * 60
            )
            
            logger.info(f"Added {role} participant {participant_id} to room {room_id}")
            return participant_id
            
        except Exception as e:
            logger.error(f"Error adding participant to room {room_id}: {e}")
            return None
    
    async def remove_participant(self, room_id: str, participant_id: str) -> bool:
        """Remove a participant from a room"""
        try:
            room = await self.get_room(room_id)
            if not room or participant_id not in room.participants:
                return False
            
            participant = room.participants[participant_id]
            was_controller = participant.role == "controller"
            
            # Remove participant
            del room.participants[participant_id]
            
            # If this was the controller, clear controller_id
            if was_controller:
                room.controller_id = None
            
            room.last_activity = datetime.now(timezone.utc).isoformat()
            
            # If no participants left, delete the room
            if not room.participants:
                room_key = self._get_room_key(room_id)
                await redis_manager.redis_client.delete(room_key)
                logger.info(f"Deleted empty room {room_id}")
            else:
                # Update room in Redis
                room_key = self._get_room_key(room_id)
                await redis_manager.redis_client.set(
                    room_key,
                    json.dumps(asdict(room)),
                    ex=24 * 60 * 60
                )
            
            logger.info(f"Removed participant {participant_id} from room {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing participant {participant_id} from room {room_id}: {e}")
            return False
    
    async def update_participant_last_seen(self, room_id: str, participant_id: str):
        """Update participant's last seen timestamp"""
        try:
            room = await self.get_room(room_id)
            if not room or participant_id not in room.participants:
                return
            
            room.participants[participant_id].last_seen = datetime.now(timezone.utc).isoformat()
            room.last_activity = datetime.now(timezone.utc).isoformat()
            
            # Update room in Redis
            room_key = self._get_room_key(room_id)
            await redis_manager.redis_client.set(
                room_key,
                json.dumps(asdict(room)),
                ex=24 * 60 * 60
            )
            
        except Exception as e:
            logger.error(f"Error updating last seen for participant {participant_id}: {e}")
    
    async def get_room_participants(self, room_id: str) -> List[Participant]:
        """Get list of participants in a room"""
        try:
            room = await self.get_room(room_id)
            if not room:
                return []
            
            return list(room.participants.values())
            
        except Exception as e:
            logger.error(f"Error getting participants for room {room_id}: {e}")
            return []
    
    async def is_controller(self, room_id: str, participant_id: str) -> bool:
        """Check if participant is the controller of the room"""
        try:
            room = await self.get_room(room_id)
            if not room:
                return False
            
            return room.controller_id == participant_id
            
        except Exception as e:
            logger.error(f"Error checking controller status: {e}")
            return False

# Global room manager instance
room_manager = RoomManager()