#!/usr/bin/env python3
"""
Seed the database with initial AI prompts.
This is run manually to set up the database, NOT automatically by the application.

Usage:
  uv run python seed_prompts.py
"""

import asyncio
import os
from app.services.database import init_database
from app.models.schemas import AIPrompt, PromptStatus, PromptParameters, ResponseFormat
from app.config import settings


async def seed_prompts():
    """Seed the database with initial prompts"""
    print("🌱 Seeding database with initial AI prompts...")
    
    if not settings.mongo_uri:
        print("❌ MONGO_URI not configured. Please set up your .env file.")
        return
    
    # Initialize database
    db = await init_database(settings.mongo_uri)
    
    prompts_to_create = [
        AIPrompt(
            name="contribution_triage_agent",
            version=1,
            status=PromptStatus.ACTIVE,
            description="Analyzes a new user contribution to decide the next AI action. Uses a fast, cheap model.",
            parameters=PromptParameters(
                model="openai/gpt-4o-mini",
                temperature=0.1,
                max_tokens=100,
                response_format=ResponseFormat(type="json_object")
            ),
            expected_vars=["goal", "latest_contribution_text"],
            template="""You are a triage agent for a collaboration tool. Analyze the 'LATEST CONTRIBUTION' in the context of the 'GOAL' and decide on an action.

Goal: {{ goal }}
Latest contribution: {{ latest_contribution_text }}

Actions:
- LOG_ONLY: Just log the message, no AI response needed
- ANSWER_DIRECTLY: Provide a direct answer to a question
- SYNTHESIZE: Generate a full synthesis of the conversation

Respond only with a JSON object: {"action": "CHOSEN_ACTION"}"""
        ),
        
        AIPrompt(
            name="direct_response_agent",
            version=1,
            status=PromptStatus.ACTIVE,
            description="Provides direct, helpful responses to questions based on conversation context.",
            parameters=PromptParameters(
                model="openai/gpt-4o",
                temperature=0.7,
                max_tokens=1000
            ),
            expected_vars=["context"],
            template="""Based on the conversation context below, provide a direct, helpful response to the latest message.

{{ context }}

Please provide a direct, helpful response to the latest message."""
        ),
        
        AIPrompt(
            name="synthesis_facilitator_default",
            version=1,
            status=PromptStatus.ACTIVE,
            assertivenessLevel=2,
            description="The default prompt for generating a full synthesis using GPT-4o with structured JSON output.",
            parameters=PromptParameters(
                model="openai/gpt-4o",
                temperature=0.2,
                max_tokens=2048,
                response_format=ResponseFormat(type="json_object")
            ),
            expected_vars=["goal", "history"],
            template="""You are Forge, an AI facilitator. Your goal is to guide the team to achieve: {{ goal }}

The full conversation history is below:
{{ history }}

Synthesize the current state, emerging consensus, and outstanding questions into a structured JSON object with these fields:
- currentState: Brief summary of where the discussion stands
- emergingConsensus: What the team seems to be agreeing on
- outstandingQuestions: Array of questions that still need answers
- nextStepsNeeded: What actions should happen next

Respond only with valid JSON."""
        )
    ]
    
    created_count = 0
    skipped_count = 0
    
    for prompt in prompts_to_create:
        # Check if prompt already exists
        existing = await db.get_active_prompt(prompt.name)
        if existing:
            print(f"⏭️  Skipped '{prompt.name}' (already exists)")
            skipped_count += 1
        else:
            await db.create_prompt(prompt)
            print(f"✅ Created '{prompt.name}' using model '{prompt.parameters.model}'")
            created_count += 1
    
    print(f"\n🎉 Seeding complete!")
    print(f"   Created: {created_count} prompts")
    print(f"   Skipped: {skipped_count} prompts (already existed)")
    
    await db.disconnect()


def main():
    """Main entry point for the seed script"""
    asyncio.run(seed_prompts())


if __name__ == "__main__":
    main() 