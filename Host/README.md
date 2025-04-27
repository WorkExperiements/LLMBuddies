# Local LLM Host

A web application for hosting and interacting with a local LLM through a web interface.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Before running the application, you'll need to:
1. Download your preferred LLM model
2. Update the `load_model()` function in `main.py` with your model configuration

## Running the Application

1. Start the server:
```bash
python main.py
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

## Features

- Web-based chat interface
- Local LLM integration
- Real-time chat responses
- Simple and intuitive UI

## Project Structure

- `main.py`: FastAPI application and server setup
- `templates/`: HTML templates for the web interface
- `static/`: Static files (CSS, JS, etc.)
- `requirements.txt`: Project dependencies