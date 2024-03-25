Lenox Project Overview
Lenox is an advanced AI companion designed to provide users with insights into cryptocurrency markets, social media sentiment, and development activity through real-time data analysis and personalized conversations. It integrates with various external APIs and leverages the power of Large Language Models (LLMs) for dynamic interaction and data processing.
Key Features and Integrations
Cryptocurrency Market Analysis: Utilizes APIs such as CryptoCompare, CoinPaprika, Messari, and Etherscan to fetch market data, historical statistics, trading pairs, and blockchain transactions.
Social Media and Sentiment Analysis: Integrates with platforms like LunarCrush to analyze social media sentiment and identify influential crypto assets.
Dynamic Conversations: Employs a sophisticated PromptEngine to generate personalized and context-aware conversations, enhancing user engagement.
Document Management: Supports file uploading through LLMA-Index for managing and processing documents, as seen in documents.py.
Data Persistence: Uses SQLAlchemy or SQLite for storing conversation history and user interactions, facilitating a contextual and continuous user experience.
Architecture and Components
External API Tools: Modules like cryptocompare_tools.py, messari_tools.py, etherscan_tools.py, coinpaprika_tools.py, and lunarcrush_tools.py are dedicated to interfacing with their respective APIs, extracting and processing data for Lenox's analytical features.
Conversational Engine: The PromptEngine in prompts.py is central to Lenox's ability to engage users, dynamically generating prompts based on user queries and the application's context.
Memory and History: Leveraging SQLChatMessageHistory ( lenox_memory.py) within a database framework (SQLAlchemy/SQLite) to maintain a record of interactions, enabling Lenox to provide contextually relevant responses and remember past conversations.
Document Handling: documents.py outlines the functionality for uploading, indexing, and retrieving documents, allowing Lenox to access and reference a wide range of informational resources.
