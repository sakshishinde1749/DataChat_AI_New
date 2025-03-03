# DataChat AI 🤖

DataChat AI is an intelligent data analysis platform that allows users to interact with their data through natural language conversations. Powered by Google's Gemini AI, it converts natural language queries into SQL and provides clear, understandable insights.

<img src="./assets/demo-screenshot.png" alt="DataChat AI Demo" width="800"/>

## ✨ Features

- 🗣️ **Natural Language Queries**: Ask questions about your data in plain English
- 🔄 **Smart SQL Generation**: Automatically converts questions to optimized SQL queries
- 💬 **Chat Interface**: Modern, ChatGPT-like conversation experience
- 📊 **Instant Analysis**: Get real-time insights from your data
- 🧠 **Context-Aware**: Maintains conversation context for follow-up questions
- 📁 **Multiple File Support**: Handles both CSV and PDF files (PDF support coming soon)
- ⏰ **24-Hour History**: Maintains chat history with automatic cleanup
- 🎨 **Modern UI**: Clean, intuitive interface with dark mode

## 🛠️ Tech Stack

### Frontend

- React.js
- Axios for API calls
- Modern CSS with dark theme
- Responsive design

### Backend

- Python/Flask
- Google Gemini AI
- SQLite for data storage
- Pandas for data manipulation

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js and npm
- Google Gemini API key

### Installation

1. Clone the repositorygit clone

- https://github.com/sakshishinde1749/DataChat_AI.git
- cd datachat-ai

2. Set up the backend

- cd backend
- python -m venv venv
- source venv/bin/activate # On Windows use: venv\Scripts\activate
- pip install -r requirements.txt

3. Create a .env file in the backend directory

- env
- GEMINI_API_KEY=your_gemini_api_key_here

4. Set up the frontend

- cd frontend
- npm install

### Running the Application

1. Start the backend server

- cd backend
- python app.py

2. Start the frontend development server

- cd frontend
  -npm start

The application will be available at http://localhost:3000

## 📖 Usage

1. Upload your data file (CSV)
2. Ask questions in natural language
3. Get instant analysis with:
   - Generated SQL query
   - Data results
   - AI-powered explanation
4. Continue the conversation with follow-up questions

### Example Questions

- "What are the total sales in 2024?"
- "Show me the best-selling products"
- "Compare January and February sales"
- "What is the average order value?"
- "Which product generated the highest revenue?"

## 📁 Project Structure

datachat-ai/

- ├── backend/
- │ ├── app.py # Flask application
- │ ├── database.py # Database operations
- │ ├── gemini_service.py# AI service integration
- │ └── requirements.txt # Python dependencies
- ├── frontend/
- │ ├── public/
- │ ├── src/
- │ │ ├── components/ # React components
- │ │ ├── App.js
- │ │ └── App.css
- │ └── package.json
- └── README.md

Also, create a requirements.txt file in your backend directory:

- pip install -r requirements.txt

## 🤝 Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes and commit them
