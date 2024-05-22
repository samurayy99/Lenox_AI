import json
import logging
from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict
from typing import Any, Dict, List

Base = declarative_base()

class Message(Base):
    __tablename__ = 'message_store'
    id = Column(Integer, primary_key=True)
    session_id = Column(Text, index=True)
    message = Column(Text)

    def __repr__(self):
        return f"<Message(session_id='{self.session_id}', message='{self.message}')>"

class SQLChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, connection_string: str):
        self.session_id = session_id
        self.engine = create_engine(connection_string, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the database."""
        try:
            with self.Session() as session:
                db_message = Message(session_id=self.session_id, message=json.dumps(message_to_dict(message)))
                session.add(db_message)
                session.commit()
            logging.debug(f"Message added successfully: {message}")
        except Exception as e:
            logging.error(f"Failed to add message: {e}")

    def messages(self, limit: int = 10) -> List[BaseMessage]:
        """Retrieve messages, ordered by most recent."""
        try:
            with self.Session() as session:
                db_messages = session.query(Message).filter(
                    Message.session_id == self.session_id
                ).order_by(Message.id.desc()).limit(limit).all()
                db_messages.reverse()
                messages = [messages_from_dict([json.loads(db_message.message)])[0] for db_message in db_messages]
                logging.debug(f"Retrieved messages: {messages}")
                return messages
        except Exception as e:
            logging.error(f"Failed to retrieve messages: {e}")
            return []

    def clear(self) -> None:
        """Clear all messages associated with the session."""
        try:
            with self.Session() as session:
                session.query(Message).filter(Message.session_id == self.session_id).delete()
                session.commit()
            logging.debug("All session messages cleared successfully.")
        except Exception as e:
            logging.error(f"Failed to clear messages: {e}")