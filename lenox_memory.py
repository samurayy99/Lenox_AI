import json
import logging
from typing import List

from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

Base = declarative_base()

class Message(Base):
    """Represents a message in the database."""
    __tablename__ = 'message_store'
    id = Column(Integer, primary_key=True)
    session_id = Column(Text, index=True)
    message = Column(Text)

    def __repr__(self):
        return f"<Message(session_id='{self.session_id}', message='{self.message}')>"

class SQLChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in a SQL database."""
    def __init__(self, session_id: str, connection_string: str):
        self.session_id = session_id
        self.engine = create_engine(connection_string, echo=False)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the database."""
        try:
            with self.session() as session:
                db_message = Message(
                    session_id=self.session_id,
                    message=json.dumps(message_to_dict(message))
                )
                session.add(db_message)
                session.commit()
            logging.debug("Message added successfully: %s", message)
        except SQLAlchemyError as e:
            logging.error("Failed to add message: %s", str(e))

    def messages(self, limit: int = 50) -> List[BaseMessage]:
        """Retrieve messages, ordered by most recent."""
        try:
            with self.session() as session:
                db_messages = (
                    session.query(Message)
                    .filter(Message.session_id == self.session_id)
                    .order_by(Message.id.desc())
                    .limit(limit)
                    .all()
                )
                db_messages.reverse()  # Reverse to maintain the order from oldest to newest
                messages = [messages_from_dict([json.loads(str(db_message.message))])[0] for db_message in db_messages]
                logging.debug("Retrieved messages: %s", messages)
                return messages
        except SQLAlchemyError as e:
            logging.error("Failed to retrieve messages: %s", str(e))
            return []

    def clear(self) -> None:
        """Clear all messages associated with the session."""
        try:
            with self.session() as session:
                session.query(Message).filter(Message.session_id == self.session_id).delete()
                session.commit()
            logging.debug("All session messages cleared successfully.")
        except SQLAlchemyError as e:
            logging.error("Failed to clear messages: %s", str(e))

