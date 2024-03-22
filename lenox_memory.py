import json
import logging
from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict
from typing import List, Dict, Any

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
        self.engine = create_engine(connection_string, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
       
    
    def get_trimmed_messages(self, limit: int = 15) -> List[BaseMessage]:
        """
        Retrieve the latest 'limit' messages from the chat history, trimming if necessary.
        """
        try:
            with self.Session() as session:
                db_messages = session.query(Message).filter(
                    Message.session_id == self.session_id
                ).order_by(Message.id.desc()).limit(limit).all()
                db_messages = list(reversed(db_messages))
                return [messages_from_dict([json.loads(db_message.message)])[0] for db_message in db_messages]
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []    
        
        

    def add_message(self, message: BaseMessage) -> None:
        try:
            with self.Session() as session:
                db_message = Message(session_id=self.session_id, message=json.dumps(message_to_dict(message)))
                session.add(db_message)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to add message: {e}")

    def messages(self, limit: int = 15) -> List[BaseMessage]:
        try:
            with self.Session() as session:
                # Abfrage anpassen, um nur die letzten `limit` Nachrichten zurückzugeben
                db_messages = session.query(Message).filter(Message.session_id == self.session_id).order_by(Message.id.desc()).limit(limit).all()
                # Umkehren der Liste, da die neuesten Nachrichten zuerst kommen
                db_messages = list(reversed(db_messages))
                return [messages_from_dict([json.loads(db_message.message)])[0] for db_message in db_messages]
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []

    def clear(self) -> None:
        try:
            with self.Session() as session:
                session.query(Message).filter(Message.session_id == self.session_id).delete()
                session.commit()
        except Exception as e:
            logger.error(f"Failed to clear messages: {e}")
            
            
    
    def load_memory_variables(self) -> Dict[str, Any]:
        # Implementiere die Methode, um Speichervariablen zu laden
        with self.Session() as session:
            context = session.query(Context).filter(Context.session_id == self.session_id).first()
            return json.loads(context.variables) if context else {}

    def save_context(self, context: Dict[str, Any]) -> None:
        # Implementiere die Methode, um den Kontext zu speichern
        with self.Session() as session:
            existing_context = session.query(Context).filter(Context.session_id == self.session_id).first()
            if existing_context:
                existing_context.variables = json.dumps(context)
            else:
                new_context = Context(session_id=self.session_id, variables=json.dumps(context))
                session.add(new_context)
            session.commit()
        
            