import json
import logging
from sqlalchemy import Column, Integer, Text, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict
from typing import List, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)
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
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def add_message(self, message: BaseMessage) -> None:
        try:
            with self.Session() as session:
                db_message = Message(session_id=self.session_id, message=json.dumps(message_to_dict(message)))
                session.add(db_message)
                session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to add message due to a database error: {e}")
        except Exception as e:
            logger.error(f"Failed to add message: {e}")

    @lru_cache(maxsize=32)
    def messages(self, limit: int = 10) -> List[BaseMessage]:
        messages_list = []
        try:
            with self.Session() as session:
                query_result = session.query(Message).filter(Message.session_id == self.session_id).order_by(Message.id.desc()).limit(limit)
                for db_message in reversed(query_result.all()):
                    messages_list.append(messages_from_dict([json.loads(db_message.message)])[0])
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve messages due to a database error: {e}")
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
        return messages_list

    def clear(self) -> None:
        try:
            with self.Session() as session:
                session.query(Message).filter(Message.session_id == self.session_id).delete()
                session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to clear messages due to a database error: {e}")
        except Exception as e:
            logger.error(f"Failed to clear messages: {e}")

    def load_memory_variables(self) -> Dict[str, Any]:
        # Example implementation (adjust according to your schema and requirements)
        try:
            with self.Session() as session:
                # Assuming there's a method to get memory variables from the session
                # Replace the following line with the actual query to load memory variables
                memory_variables = session.query(Message).filter(Message.session_id == self.session_id).all()
                return {var.name: var.value for var in memory_variables}
        except SQLAlchemyError as e:
            logger.error(f"Failed to load memory variables due to a database error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load memory variables: {e}")
            return {}

    def memory_variables(self) -> List[str]:
        # Example implementation (adjust according to your schema and requirements)
        try:
            with self.Session() as session:
                # Assuming there's a method to list memory variables from the session
                # Replace the following line with the actual query to list memory variables
                variables = session.query(Message).filter(Message.session_id == self.session_id).all()
                return [var.name for var in variables]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list memory variables due to a database error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to list memory variables: {e}")
            return []

    def save_context(self, context: Dict[str, Any]) -> None:
        # Example implementation (adjust according to your schema and requirements)
        try:
            with self.Session() as session:
                # Assuming there's a method to save context to the session
                # Replace the following lines with the actual logic to save the context
                for key, value in context.items():
                    # Here you would either update the existing entry or create a new one
                    session.merge(Message(session_id=self.session_id, message=json.dumps({key: value})))
                session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to save context due to a database error: {e}")
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
