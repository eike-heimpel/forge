import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import PyMongoError
from bson import ObjectId
from loguru import logger

from app.models.schemas import (
    Forge, Contribution, AIPrompt, ContributionType, 
    PromptStatus, TriageAction, PyObjectId
)


class DatabaseService:
    """Async MongoDB service for Forge application"""
    
    def __init__(self, mongo_uri: str, database_name: str = "forge"):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        
        # Collection references
        self.forges: Optional[AsyncIOMotorCollection] = None
        self.contributions: Optional[AsyncIOMotorCollection] = None
        self.ai_prompts: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            
            # Initialize collection references
            self.forges = self.db.forges
            self.contributions = self.db.contributions
            self.ai_prompts = self.db.ai_prompts
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {self.database_name}")
            
            # Create indexes for performance
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Forges collection indexes
            await self.forges.create_index("members.userId")
            await self.forges.create_index("status")
            await self.forges.create_index("createdAt")
            
            # Contributions collection indexes  
            await self.contributions.create_index("forgeId")
            await self.contributions.create_index("authorId")
            await self.contributions.create_index("type")
            await self.contributions.create_index("createdAt")
            await self.contributions.create_index([("forgeId", 1), ("createdAt", -1)])
            
            # AI Prompts collection indexes
            await self.ai_prompts.create_index("name")
            await self.ai_prompts.create_index("status")
            await self.ai_prompts.create_index([("name", 1), ("version", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    # ===============================
    # FORGE OPERATIONS
    # ===============================
    
    async def get_forge_by_id(self, forge_id: ObjectId) -> Optional[Forge]:
        """Get forge by ID"""
        try:
            doc = await self.forges.find_one({"_id": forge_id})
            if doc:
                # Convert ObjectIds to strings for Pydantic validation
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "lastSynthesisId" in doc and doc["lastSynthesisId"]:
                    doc["lastSynthesisId"] = str(doc["lastSynthesisId"])
                # Convert member ObjectIds
                if "members" in doc:
                    for member in doc["members"]:
                        if "userId" in member:
                            member["userId"] = str(member["userId"])
                return Forge(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting forge {forge_id}: {e}")
            return None

    async def user_has_forge_access(self, forge_id: ObjectId, user_id: ObjectId) -> bool:
        """Check if user has access to forge (Golden Rule enforcement)"""
        try:
            doc = await self.forges.find_one({
                "_id": forge_id,
                "members.userId": user_id
            })
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking forge access for user {user_id} on forge {forge_id}: {e}")
            return False

    # ===============================
    # CONTRIBUTION OPERATIONS
    # ===============================
    
    async def create_contribution(self, contribution: Contribution) -> Optional[ObjectId]:
        """Insert a new contribution"""
        try:
            # Convert Pydantic model to dict
            doc = contribution.model_dump(by_alias=True, exclude_none=True)
            if "_id" not in doc:
                doc["_id"] = ObjectId()
            
            result = await self.contributions.insert_one(doc)
            logger.info(f"Created contribution {result.inserted_id} in forge {contribution.forgeId}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Error creating contribution: {e}")
            return None

    async def get_contribution_by_id(self, contribution_id: ObjectId) -> Optional[Contribution]:
        """Get contribution by ID"""
        try:
            doc = await self.contributions.find_one({"_id": contribution_id})
            if doc:
                # Convert ObjectIds to strings for Pydantic validation
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "forgeId" in doc:
                    doc["forgeId"] = str(doc["forgeId"])
                if "authorId" in doc:
                    doc["authorId"] = str(doc["authorId"])
                if "sourceContributionIds" in doc and doc["sourceContributionIds"]:
                    doc["sourceContributionIds"] = [str(oid) for oid in doc["sourceContributionIds"]]
                return Contribution(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting contribution {contribution_id}: {e}")
            return None

    async def get_forge_contributions(
        self, 
        forge_id: ObjectId, 
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[Contribution]:
        """Get contributions for a forge, ordered by creation time"""
        try:
            query = {"forgeId": forge_id}
            if since:
                query["createdAt"] = {"$gt": since}
            
            cursor = self.contributions.find(query).sort("createdAt", 1)
            if limit:
                cursor = cursor.limit(limit)
            
            docs = await cursor.to_list(length=None)
            contributions = []
            for doc in docs:
                # Convert ObjectIds to strings for Pydantic validation
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "forgeId" in doc:
                    doc["forgeId"] = str(doc["forgeId"])
                if "authorId" in doc:
                    doc["authorId"] = str(doc["authorId"])
                if "sourceContributionIds" in doc and doc["sourceContributionIds"]:
                    doc["sourceContributionIds"] = [str(oid) for oid in doc["sourceContributionIds"]]
                contributions.append(Contribution(**doc))
            return contributions
            
        except Exception as e:
            logger.error(f"Error getting contributions for forge {forge_id}: {e}")
            return []

    async def get_latest_contributions(self, forge_id: ObjectId, count: int = 10) -> List[Contribution]:
        """Get the most recent contributions for a forge"""
        try:
            cursor = self.contributions.find({"forgeId": forge_id}).sort("createdAt", -1).limit(count)
            docs = await cursor.to_list(length=None)
            
            contributions = []
            for doc in reversed(docs):  # Reverse to get chronological order
                # Convert ObjectIds to strings for Pydantic validation
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "forgeId" in doc:
                    doc["forgeId"] = str(doc["forgeId"])
                if "authorId" in doc:
                    doc["authorId"] = str(doc["authorId"])
                if "sourceContributionIds" in doc and doc["sourceContributionIds"]:
                    doc["sourceContributionIds"] = [str(oid) for oid in doc["sourceContributionIds"]]
                contributions.append(Contribution(**doc))
            return contributions
        except Exception as e:
            logger.error(f"Error getting latest contributions for forge {forge_id}: {e}")
            return []

    # ===============================
    # AI PROMPT OPERATIONS
    # ===============================
    
    async def get_active_prompt(self, name: str) -> Optional[AIPrompt]:
        """Get the active version of a prompt by name"""
        try:
            doc = await self.ai_prompts.find_one({
                "name": name,
                "status": PromptStatus.ACTIVE
            }, sort=[("version", -1)])  # Get highest version number
            
            if doc:
                # Convert ObjectId to string for Pydantic validation
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                return AIPrompt(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting active prompt '{name}': {e}")
            return None

    async def create_prompt(self, prompt: AIPrompt) -> Optional[ObjectId]:
        """Create a new prompt in the database"""
        try:
            doc = prompt.model_dump(by_alias=True, exclude={"id"})
            doc["createdAt"] = datetime.utcnow()
            
            result = await self.ai_prompts.insert_one(doc)
            logger.info(f"Created prompt '{prompt.name}' version {prompt.version}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Error creating prompt '{prompt.name}': {e}")
            return None

    async def list_active_prompts(self) -> List[AIPrompt]:
        """Get all active prompts (latest version of each)"""
        try:
            # Aggregate to get the latest version of each prompt name
            pipeline = [
                {"$match": {"status": PromptStatus.ACTIVE}},
                {"$sort": {"name": 1, "version": -1}},
                {"$group": {
                    "_id": "$name",
                    "latest_doc": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest_doc"}},
                {"$sort": {"name": 1}}
            ]
            
            docs = await self.ai_prompts.aggregate(pipeline).to_list(length=None)
            
            prompts = []
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                prompts.append(AIPrompt(**doc))
            
            return prompts
            
        except Exception as e:
            logger.error(f"Error listing active prompts: {e}")
            return []

    async def get_prompt_by_name_and_version(self, name: str, version: Optional[int] = None) -> Optional[AIPrompt]:
        """Get a specific prompt by name and version. If version is None, gets the latest active version."""
        try:
            query = {"name": name}
            if version is not None:
                query["version"] = version
            else:
                query["status"] = PromptStatus.ACTIVE
            
            sort_order = [("version", -1)] if version is None else None
            
            doc = await self.ai_prompts.find_one(query, sort=sort_order)
            
            if doc:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                return AIPrompt(**doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting prompt '{name}' version {version}: {e}")
            return None

    # ===============================
    # UTILITY METHODS
    # ===============================
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

    async def get_forge_goal(self, forge_id: ObjectId) -> Optional[str]:
        """Get just the goal text for a forge (lightweight query)"""
        try:
            doc = await self.forges.find_one({"_id": forge_id}, {"goal": 1})
            return doc.get("goal") if doc else None
        except Exception as e:
            logger.error(f"Error getting forge goal for {forge_id}: {e}")
            return None

    async def update_forge_last_synthesis(self, forge_id: ObjectId, synthesis_id: ObjectId):
        """Update the last synthesis ID for a forge"""
        try:
            await self.forges.update_one(
                {"_id": forge_id},
                {"$set": {"lastSynthesisId": synthesis_id}}
            )
            logger.info(f"Updated last synthesis for forge {forge_id} to {synthesis_id}")
        except Exception as e:
            logger.error(f"Error updating last synthesis for forge {forge_id}: {e}")


# Global database service instance
db_service: Optional[DatabaseService] = None


async def get_database() -> DatabaseService:
    """Dependency to get database service"""
    global db_service
    if db_service is None:
        raise RuntimeError("Database service not initialized")
    return db_service


async def init_database(mongo_uri: str) -> DatabaseService:
    """Initialize database service"""
    global db_service
    db_service = DatabaseService(mongo_uri)
    await db_service.connect()
    return db_service 