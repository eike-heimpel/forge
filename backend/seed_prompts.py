#!/usr/bin/env python3
"""
Seed the database with initial AI prompts.
This is run manually to set up the database, NOT automatically by the application.

Usage:
  uv run python seed_prompts.py
  uv run python seed_prompts.py --force  # Overwrite existing prompts
"""

import argparse
import asyncio
import os
from app.services.database import init_database
from app.models.schemas import AIPrompt, PromptStatus, PromptParameters, ResponseFormat
from app.config import settings


async def seed_prompts(force_overwrite: bool = False):
    """Seed the database with initial prompts"""
    print("🌱 Seeding database with initial AI prompts...")
    
    if force_overwrite:
        print("⚠️  Force mode enabled - will clear existing prompts and recreate all")
    
    if not settings.mongo_uri:
        print("❌ MONGO_URI not configured. Please set up your .env file.")
        return
    
    # Initialize database
    db = await init_database(settings.mongo_uri)
    
    # If force mode, clear the entire prompts collection
    if force_overwrite:
        try:
            result = await db.ai_prompts.delete_many({})
            print(f"🗑️  Cleared {result.deleted_count} existing prompts from database")
        except Exception as e:
            print(f"❌ Error clearing prompts collection: {e}")
            return
    
    prompts_to_create = [
        AIPrompt(
            name="contribution_triage_agent",
            version=1,
            status=PromptStatus.ACTIVE,
            description="Analyzes a new user contribution to decide the next AI action. Uses a fast, cheap model.",
            parameters=PromptParameters(
                model="google/gemini-2.5-flash-lite",
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
            description="AI facilitator that provides helpful, contextual responses to team members' questions using project context and briefings.",
            parameters=PromptParameters(
                model="google/gemini-2.5-flash",
                temperature=0.7,
                max_tokens=1000
            ),
            expected_vars=["role", "current_briefing", "synthesis", "chat_history_text"],
            template="""You are the AI facilitator for {{ role['name'] }} ({{ role['title'] }}). They have asked you a question and expect a helpful response.

**Current Briefing for {{ role['name'] }}**:
{{ current_briefing }}

**Project Context**:
{{ synthesis }}

**Chat History**:
{{ chat_history_text }}

**CRITICAL CONSTRAINTS:**
- For FACTUAL questions about the project: Only use information from the briefing, project context, and chat history above
- For PROCESS/FACILITATION questions: You may use your knowledge of facilitation methods and project management
- If factual information isn't available in the provided context, clearly state "I don't have that information from our discussion" rather than guessing
- Never inject external knowledge about the subject matter or make assumptions beyond what was shared

**Your Task**: Provide a concise, helpful response to their latest question:

- Reference their briefing and project context when relevant
- Ask follow-up questions to move their work forward  
- Stay facilitative, not directive - help them think through it
- Keep it to 2-3 sentences max
- Be directly helpful and specific
- Be honest about information gaps

Respond with your answer directly (no JSON formatting needed):"""
        ),
        
        AIPrompt(
            name="synthesis_facilitator_default",
            version=1,
            status=PromptStatus.ACTIVE,
            assertivenessLevel=2,
            description="Comprehensive synthesis prompt that creates briefing packages with overall context and personalized briefings for each team member.",
            parameters=PromptParameters(
                model="google/gemini-2.5-flash",
                temperature=0.2,
                max_tokens=2048,
                response_format=ResponseFormat(type="json_object")
            ),
            expected_vars=["goal", "roles_text", "contributions_text"],
            template="""You are the lead AI facilitator managing a team discussion. Create a comprehensive briefing package that includes overall context and personalized briefings for each team member.

**Session Goal**: {{ goal }}

**Team**: {{ roles_text }}

**Full Conversation**: {{ contributions_text }}

**Your Task**: Output valid JSON with this exact structure:

{
  "overallContext": "COMPREHENSIVE facilitator notes for full team context. Include: key decisions made, critical information shared, specific next steps identified, open questions, context dependencies between roles, priorities, strategic context, and any important nuances. Use bullet points and structure this well - it should be thorough and detailed to give complete situational awareness.",
  
  "individualBriefings": {
    "ROLE_ID_1": {
      "briefing": "Hi [Name], 2-3 concise sentences max about what's most relevant to your role right now. Be direct and specific.",
      "questions": ["Specific question 1 to move their work forward", "Specific question 2 if needed"],
      "todos": ["Concrete action item 1 if clear from context", "Action item 2 if applicable"],
      "priorities": "Single sentence about what they should focus on first"
    },
    "ROLE_ID_2": {
      "briefing": "Hi [Name], ...",
      "questions": ["..."],
      "todos": ["..."],
      "priorities": "..."
    }
  }
}

**Guidelines:**

**For Overall Context (be comprehensive):**
- Include all key decisions, information, and strategic context
- Use bullet points and clear structure
- Cover dependencies between team members
- Note priorities and open questions  
- Be thorough - this is the master context for facilitators
- Include nuances and important details that inform the situation

**For Individual Briefings (be concise):**
- Keep briefings to 2-3 sentences MAX - be concise and scannable
- Focus on what's immediately actionable and relevant to their role
- Questions should be specific and focused (1-2 max)
- Todos only if they clearly emerged from discussion
- Priorities should be one clear, focused sentence
- Make it quick to read and understand at a glance

**CRITICAL: Output ONLY the raw JSON object - no markdown code blocks, no ```json```, no additional text or formatting. Start directly with { and end with }.**"""
        )
    ]
    
    # Now insert all prompts (either fresh insert or complete recreation after force clear)
    created_count = 0
    error_count = 0
    
    for prompt in prompts_to_create:
        try:
            if not force_overwrite:
                # Check if prompt already exists (only when not in force mode)
                existing = await db.get_active_prompt(prompt.name)
                if existing:
                    print(f"⏭️  Skipped '{prompt.name}' (already exists)")
                    continue
            
            await db.create_prompt(prompt)
            print(f"✅ Created '{prompt.name}' using model '{prompt.parameters.model}'")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Error creating prompt '{prompt.name}': {e}")
            error_count += 1
    
    print(f"\n🎉 Seeding complete!")
    if force_overwrite:
        print(f"   Recreated: {created_count} prompts (force mode)")
    else:
        print(f"   Created: {created_count} prompts")
    
    if error_count > 0:
        print(f"   Errors: {error_count} prompts failed")
    
    skipped_count = len(prompts_to_create) - created_count - error_count
    if skipped_count > 0 and not force_overwrite:
        print(f"   Skipped: {skipped_count} prompts (already existed)")


def main():
    """Main entry point for the seed script"""
    parser = argparse.ArgumentParser(description="Seed database with AI prompts")
    parser.add_argument("--force", action="store_true", 
                      help="Overwrite existing prompts instead of skipping them")
    
    args = parser.parse_args()
    asyncio.run(seed_prompts(force_overwrite=args.force))


if __name__ == "__main__":
    main() 