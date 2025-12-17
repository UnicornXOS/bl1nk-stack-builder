from bedrock_agentcore.memory import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole

# Initialize the session manager
manager = MemorySessionManager(
    memory_id="your-memory-id",  # Use existing memory id
    region_name="us-east-1"
)

# Create a session for a specific actor
session = manager.create_memory_session(
    actor_id="user-123",
    session_id="session-456"  # Optional - will generate UUID if not provided
)

# Add conversation turns
session.add_turns([
    ConversationalMessage("I love eating apples and cherries", MessageRole.USER),
    ConversationalMessage("Apples are very good for you!", MessageRole.ASSISTANT),
    ConversationalMessage("What's your favorite thing about apples?", MessageRole.USER),
    ConversationalMessage("I enjoy their flavor and nutritional benefits", MessageRole.ASSISTANT)
])

# Search long-term memories (after memory extraction has occurred)
memories = session.search_long_term_memories(
    query="what food does the user like",
    namespace_prefix="/food/user-123",
    top_k=5
)

# Or search across multiple users
memories = manager.search_long_term_memories(
    query="Food preferences",
    namespace_prefix="/food/",  # Search all food-related memories
    top_k=10
)