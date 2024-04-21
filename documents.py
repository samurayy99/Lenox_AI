from llama_index.llms.openai import OpenAI
import os
import textract
import logging
from werkzeug.utils import secure_filename
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.langchain_helpers.agents import IndexToolConfig, LlamaIndexTool

openai_api_key = os.getenv("OPENAI_API_KEY")
current_script_path = os.path.dirname(os.path.abspath(__file__))
document_folder = os.path.join(current_script_path, 'documents') + '/'
data_folder = os.path.join(current_script_path, 'data') + '/'
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class DocumentHandler:
    def __init__(self, document_folder, data_folder):
        self.document_folder = document_folder
        self.data_folder = data_folder
        self._load_or_create_index()

    def _load_or_create_index(self):
        docstore_path = os.path.join(self.data_folder, 'docstore.json')
        if os.path.exists(docstore_path):
            storage_context = StorageContext.from_defaults(persist_dir=self.data_folder)
            self.index = load_index_from_storage(storage_context)
        else:
            if not os.path.exists(self.data_folder):
                os.makedirs(self.data_folder)
            documents = SimpleDirectoryReader(self.document_folder).load_data()
            if documents:
                self.index = VectorStoreIndex.from_documents(documents)
                self.index.storage_context.persist(persist_dir=self.data_folder)
            else:
                logging.info("No documents found to create an initial index.")

    def query(self, prompt):
        if self.index is None:
            logging.error("Index not initialized. Please upload a document first.")
            return "Index not initialized. Please upload a document first."
        
        tool_config = IndexToolConfig(
            query_engine=self.index.as_query_engine(),
            name="Vector Index",
            description="Useful for querying documents",
            tool_kwargs={"return_direct": True},
        )
        tool = LlamaIndexTool.from_tool_config(tool_config)
        response = tool(prompt)
        return response

    def _index_documents(self):
        logging.info("Indexing documents...")
        documents = SimpleDirectoryReader(self.document_folder).load_data()
        if documents:
            logging.info(f"Loaded {len(documents)} documents for indexing.")
            self.index = VectorStoreIndex.from_documents(documents)
            if self.index:
                self.index.storage_context.persist(persist_dir=self.data_folder)
                logging.info(f"Documents indexed and persisted at {self.data_folder}.")
            else:
                logging.error("Failed to create index from documents.")
        else:
            logging.warning("No documents found for indexing.")

    def save_document(self, file):
        if file.content_length > MAX_FILE_SIZE:
            logging.warning("File size exceeds the maximum limit.")
            return False, "File size exceeds the maximum limit."
        filename = secure_filename(file.filename)
        save_path = os.path.join(self.document_folder, filename)
        try:
            file.save(save_path)
            self._index_documents()
            return True, f"Datei {filename} erfolgreich hochgeladen und indiziert."
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Dokuments: {e}")
            return False, f"Fehler beim Speichern des Dokuments: {e}"

    def read_document(self, filename: str):
        file_path = os.path.join(self.document_folder, filename)
        try:
            # Use textract to pull out text content from various file types
            text = textract.process(file_path)
            return text.decode('utf-8')
        except Exception as e:
            logging.error(f"Failed to read document: {e}")
            return None

    def process_uploaded_document(self, filename: str):
        content = self.read_document(filename)
        if content:
            # Hier können Sie zusätzliche Verarbeitung hinzufügen, z.B. Textanalyse
            pass  # Dies ist ein Platzhalter für Ihre Verarbeitungslogik
        else:
            logging.error("Dokumentinhalt konnte nicht verarbeitet werden.")