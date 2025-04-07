## 🧠 AI Personality Assessment:
An AI-powered web application that analyzes user responses to assess personality traits using psychological models like the Big Five or MBTI. The app consists of a React-based frontend and a Python (FastAPI) backend.

## 🚀 Getting Started
Follow the steps below to set up and run the project locally on your machine.

## 🔧 Prerequisites
Before you begin, ensure you have the following installed:

1. Node.js (v22.14.0)
2. Python (v3.13.1)
3. A terminal or command-line tool
4. An API key for OpenRouter or your preferred AI provider

## 📦 Frontend Setup (React + Vite)
1. Install Node.js
   Download and install from https://nodejs.org.
2. Clone the Repository:
   git clone
3. Install Frontend Dependencies In your terminal, run:
   npm install
4. Start the Frontend Server:
   npm run dev
5. Open the Application in Your Browser, after running the above command, a local development URL will appear in the terminal, typically like:
   http://localhost:5173/

## 🧠 Backend Setup (Python + FastAPI)
1. Open a new terminal and run:
   cd backend
2. Install Required Python Packages
   pip install -r requirements.txt  
3. Configure Environment Variables In the backend/.env file, add your API key and model name. Example:   
   OPENROUTER_API_KEY='your_api_key_here'
   OPENROUTER_MODEL_ANALYSIS=''  # or whichever model you're using
4. Start the Backend Server
   python main.py
   This will start your FastAPI backend server on a default port (usually http://127.0.0.1:8000).   

   
