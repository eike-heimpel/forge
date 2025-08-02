from pymongo import MongoClient
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        
    async def connect(self):
        if not self.client:
            self.client = MongoClient(settings.mongo_uri)
            self.db = self.client['forge-test']
            
    async def get_app_state(self, forge_id: str) -> Dict[str, Any]:
        """Get the current state for a forge"""
        try:
            await self.connect()
            collection = self.db['forge-test1']
            
            doc = collection.find_one({"_id": f"forge-{forge_id}"})
            if doc:
                # Remove MongoDB _id from the returned document
                doc.pop('_id', None)
                return doc
                
            # Return initial state if not found
            initial_state = {
                "roles": [
                    {"name": "Konrad", "title": "Product Lead", "id": "1"},
                    {"name": "Eike", "title": "General Consultant", "id": "2"},
                ],
                "contributions": [],
                "syntheses": [],
                "todos": {},
                "roleChats": [],
                "goal": "Create MVP scope for new product idea",
            }
            
            # Create the document in the database
            doc_to_insert = {"_id": f"forge-{forge_id}", **initial_state}
            collection.insert_one(doc_to_insert)
            
            return initial_state
            
        except Exception as e:
            logger.error(f"Error reading state from MongoDB: {e}")
            # Return initial state as fallback
            return {
                "roles": [
                    {"name": "Konrad", "title": "Product Lead", "id": "1"},
                    {"name": "Eike", "title": "General Consultant", "id": "2"},
                ],
                "contributions": [],
                "syntheses": [],
                "todos": {},
                "roleChats": [],
                "goal": "Create MVP scope for new product idea",
            }
    
    async def write_app_state(self, forge_id: str, state: Dict[str, Any]) -> bool:
        """Write the complete state for a forge"""
        try:
            await self.connect()
            collection = self.db['forge-test1']
            
            doc_to_write = {"_id": f"forge-{forge_id}", **state}
            collection.replace_one(
                {"_id": f"forge-{forge_id}"},
                doc_to_write,
                upsert=True
            )
            return True
            
        except Exception as e:
            logger.error(f"Error writing state to MongoDB: {e}")
            return False
    
    async def add_synthesis(self, forge_id: str, synthesis: Dict[str, Any]) -> bool:
        """Add a new synthesis to the state"""
        try:
            state = await self.get_app_state(forge_id)
            state["syntheses"].append(synthesis)
            return await self.write_app_state(forge_id, state)
            
        except Exception as e:
            logger.error(f"Error adding synthesis: {e}")
            return False
    
    async def add_todos(self, forge_id: str, synthesis_id: str, briefings: List[Dict[str, str]]) -> bool:
        """Add briefings for a synthesis"""
        try:
            state = await self.get_app_state(forge_id)
            if "todos" not in state:
                state["todos"] = {}
            state["todos"][synthesis_id] = briefings
            return await self.write_app_state(forge_id, state)
            
        except Exception as e:
            logger.error(f"Error adding todos: {e}")
            return False
    
    async def add_contribution(self, forge_id: str, author_id: str, text: str) -> bool:
        """Add a new contribution"""
        try:
            state = await self.get_app_state(forge_id)
            
            # Find the author role
            author = None
            for role in state["roles"]:
                if role["id"] == author_id:
                    author = role
                    break
                    
            if not author:
                logger.error(f"Author role {author_id} not found")
                return False
            
            new_contribution = {
                "id": str(int(datetime.now().timestamp() * 1000)),
                "timestamp": datetime.now().isoformat(),
                "authorId": author_id,
                "authorName": author["name"],
                "authorTitle": author["title"],
                "text": text,
                "role": f"{author['name']} - {author['title']}",
            }
            
            state["contributions"].append(new_contribution)
            return await self.write_app_state(forge_id, state)
            
        except Exception as e:
            logger.error(f"Error adding contribution: {e}")
            return False
    
    async def add_chat_message(self, forge_id: str, role_id: str, message: str, author: str) -> Optional[Dict[str, Any]]:
        """Add a chat message and return the updated role chat"""
        try:
            state = await self.get_app_state(forge_id)
            
            # Ensure roleChats exists
            if "roleChats" not in state:
                state["roleChats"] = []
            
            # Find or create role chat
            role_chat = None
            for chat in state["roleChats"]:
                if chat["roleId"] == role_id:
                    role_chat = chat
                    break
            
            if not role_chat:
                role_chat = {
                    "roleId": role_id,
                    "messages": [],
                    "lastBriefingId": None
                }
                state["roleChats"].append(role_chat)
            
            # Add new message
            new_message = {
                "id": str(int(datetime.now().timestamp() * 1000)),
                "author": author,
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            
            role_chat["messages"].append(new_message)
            
            # Save state
            if await self.write_app_state(forge_id, state):
                return role_chat
            return None
            
        except Exception as e:
            logger.error(f"Error adding chat message: {e}")
            return None

# Global database service instance
db_service = DatabaseService() 