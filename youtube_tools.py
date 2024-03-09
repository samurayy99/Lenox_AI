import requests
from typing import List
from langchain.agents import tool
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.tools import YouTubeSearchTool
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.chains.question_answering import load_qa_chain
import scrapetube


@tool
def search_youtube(query: str, max_results: int = 5) -> str:
    """
    Searches YouTube for videos matching the query and returns a list of video titles and URLs.

    Args:
        query (str): The search query string.
        max_results (int): Maximum number of search results to return.

    Returns:
        str: A formatted string containing titles and URLs of the top search results.
    """
    try:
        videos = scrapetube.get_search(query, limit=max_results)
        results = []
        for video in videos:
            title = video.get('title', 'No title')
            video_id = video.get('videoId', 'No video ID')
            results.append(f"Title: {title}\nURL: https://www.youtube.com/watch?v={video_id}")
        
        if not results:
            return "No videos found."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"


@tool
def process_youtube_video(url: str) -> List[Document]:
    """
    Processes a YouTube video URL and extracts its content for further analysis.

    Args:
        url (str): The URL of the YouTube video.

    Returns:
        List[Document]: A list of documents representing the video content.
    """
    try:
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
        documents = loader.load()
        return documents
    except Exception as e:
        return [Document(page_content=str(e), metadata={})] 

@tool
def query_youtube_video(url: str, question: str) -> str:
    """
    Performs a question-answering query on the content of a YouTube video.

    Args:
        url (str): The URL of the YouTube video.
        question (str): The question to ask about the video content.

    Returns:
        str: The answer to the question based on the video content.
    """
    try:
        documents = process_youtube_video(url)
        llm = OpenAI(temperature=0)
        chain = load_qa_chain(llm, chain_type="default")
        output = chain.run(input_documents=documents, question=question)
        return output
    except Exception as e:
        return f"Error querying YouTube video: {str(e)}"


class YouTubeQA:
    def __init__(self):
        """
        Initializes the YouTubeQA class for processing and querying YouTube videos.
        """
        self.llm = OpenAI(temperature=0)
        self.embeddings = OpenAIEmbeddings()
        self.db = None  # Placeholder for Chroma instance
        self.chain = None  # Placeholder for QA chain

    @tool
    def ingest_video(self, url: str) -> str:
        """
        Ingests a YouTube video, processes its content, and prepares it for question-answering.

        Args:
            url (str): The URL of the YouTube video to be ingested.

        Returns:
            str: A confirmation message indicating successful ingestion.
        """
        try:
            documents = process_youtube_video(url)
            self.db = Chroma.from_documents(documents, self.embeddings).as_retriever()
            self.chain = load_qa_chain(self.llm, chain_type="default")
            return "Video content successfully ingested and prepared for question-answering."
        except Exception as e:
            return f"Error ingesting YouTube video: {str(e)}"

    @tool
    def answer_question(self, question: str) -> str:
        """
        Answers a question based on the ingested YouTube video content.

        Args:
            question (str): The question to be answered.

        Returns:
            str: The answer to the question, or an error message if the video has not been ingested.
        """
        if not self.chain or not self.db:
            return "Please ingest a video first using the ingest_video method."
        
        try:
            docs = self.db.get_relevant_documents(question)
            output = self.chain.run(input_documents=docs, question=question)
            return output
        except Exception as e:
            return f"Error answering question: {str(e)}"

