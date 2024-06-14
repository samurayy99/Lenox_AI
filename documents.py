import os
import logging
from werkzeug.utils import secure_filename
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.core.langchain_helpers.agents import IndexToolConfig, LlamaIndexTool
from langchain_huggingface import HuggingFaceEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding



lc_embed_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)
embed_model = LangchainEmbedding(lc_embed_model)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment and directory setup
openai_api_key = os.getenv("OPENAI_API_KEY")
current_script_path = os.path.dirname(os.path.abspath(__file__))
document_folder = os.path.join(current_script_path, 'documents') + '/'
data_folder = os.path.join(current_script_path, 'data') + '/'

# Constants for file handling
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class DocumentHandler:
    def __init__(self, document_folder, data_folder):
        self.document_folder = document_folder
        self.data_folder = data_folder
        self.index = self._load_or_create_index()

    def _load_or_create_index(self):
        """Attempt to load the index from storage, or create a new index if necessary."""
        docstore_path = os.path.join(self.data_folder, 'docstore.json')
        if os.path.exists(docstore_path):
            try:
                storage_context = StorageContext.from_defaults(persist_dir=self.data_folder)
                self.index = load_index_from_storage(storage_context)
            except Exception as e:
                logging.error(f"Error loading index from storage: {e}")
                raise
        else:
            logging.info("No existing index found. Attempting to create a new index.")
            try:
                os.makedirs(self.data_folder, exist_ok=True)
                documents = SimpleDirectoryReader(self.document_folder).load_data()
                if documents:
                    self.index = VectorStoreIndex.from_documents(documents)
                else:
                    self.index = None
                if self.index:
                    self.index.storage_context.persist(persist_dir=self.data_folder)
                    logging.info("New index created and documents indexed.")
                else:
                    logging.info("No documents found to index at initialization.")
            except Exception as e:
                logging.error(f"Error creating a new index: {e}")
                raise

    def save_document(self, file):
        """Save a new document and update the index."""
        if file.content_length > MAX_FILE_SIZE:
            logging.warning("File size exceeds the maximum limit.")
            return False, "File size exceeds the maximum limit."
        if not allowed_file(file.filename):
            logging.warning("Unsupported file type.")
            return False, "Unsupported file type."

        filename = secure_filename(file.filename)
        save_path = os.path.join(self.document_folder, filename)
        try:
            file.save(save_path)
            logging.info(f"File saved to {save_path}. Initiating re-indexing.")
            self.index_documents()
            return True, "File successfully uploaded and indexed."
        except Exception as e:
            logging.error(f"Error saving document: {e}")
            return False, f"Error saving document: {e}"

    def index_documents(self):
        """Re-index all documents in the document directory."""
        logging.info("Re-indexing all documents...")
        try:
            documents = SimpleDirectoryReader(self.document_folder).load_data()
            if documents:
                self.index = VectorStoreIndex.from_documents(documents)
                self.index.storage_context.persist(persist_dir=self.data_folder)
                logging.info(f"All documents have been re-indexed and data persisted at {self.data_folder}.")
            else:
                logging.warning("No documents available for re-indexing.")
        except Exception as e:
            logging.error(f"Error re-indexing documents: {e}")
            raise

    def query(self, prompt):
        """Query the indexed data based on a given prompt."""
        if not self.index:
            logging.error("Index not initialized. No document available to query.")
            return "Index not initialized. Please upload a document first."

        try:
            tool_config = IndexToolConfig(
                query_engine=self.index.as_query_engine(),
                name="Vector Index",
                description="Useful for querying documents",
                tool_kwargs={"return_direct": True}
            )
            tool = LlamaIndexTool.from_tool_config(tool_config)
            response = tool(prompt)
            return response
        except Exception as e:
            logging.error(f"Error querying the index: {e}")
            raise
