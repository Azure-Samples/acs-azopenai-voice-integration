from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime
import uuid
from ..config.settings import Config


class CosmosDBService:
    """Service to handle CosmosDB operations for session and chat history storage."""

    def __init__(self, config: Config):
        self.client = CosmosClient(config.COSMOS_DB_URL, config.COSMOS_DB_KEY)
        self.database = self.client.create_database_if_not_exists(id=config.COSMOS_DB_DATABASE_NAME)
        self.container = self.database.create_container_if_not_exists(
            id=config.COSMOS_DB_CONTAINER_NAME,
            partition_key=PartitionKey(path="/callerId"),
            offer_throughput=400,
        )

    def create_new_session(self, caller_id: str, acs_connection_id: str):
        """Create a new session in CosmosDB."""
        session_id = acs_connection_id
        session = {
            "id": session_id,
            "callerId": caller_id,
            "callStartTime": datetime.utcnow().isoformat(),
            "callEndTime": None,
            "conversation": [],
            "userDetails": {},  # Optionally include additional user details
        }
        self.container.create_item(body=session)
        return session_id

    def append_message_to_session(self, session_id: str, caller_id: str, sender: str, message: str):
        """Append a message to an existing session's conversation."""
        query = f"SELECT * FROM c WHERE c.id = '{session_id}' AND c.callerId = '{caller_id}'"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

        if not items:
            raise ValueError("Session not found")

        session = items[0]
        session["conversation"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "sender": sender,
            "message": message,
        })

        self.container.replace_item(item=session, body=session)

    def close_session(self, session_id: str, caller_id: str):
        """Close a session by setting the end time."""
        query = f"SELECT * FROM c WHERE c.id = '{session_id}' AND c.callerId = '{caller_id}'"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))

        if not items:
            raise ValueError("Session not found")

        session = items[0]
        session["callEndTime"] = datetime.utcnow().isoformat()
        self.container.replace_item(item=session, body=session)
