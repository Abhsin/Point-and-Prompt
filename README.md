# Point and Prompt

A powerful desktop application that allows you to capture screen regions and get AI-powered descriptions using Google's Gemini AI model.

## Features

- 🔍 Screen region selection with screenshot capture
- 🤖 AI-powered image analysis using Google's Gemini model
- ⌨️ Global hotkey support (` + Left Mouse Click)
- 🖼️ Interactive region selection interface
- 📝 Detailed image descriptions and analysis

## Prerequisites

- Python 3.7 or higher
- Tesseract OCR engine (for OCR functionality)
- Google Cloud API key with Gemini API access

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd point-and-prompt
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Press `` + Left Mouse Click to capture a screen region
3. Select the area you want to analyze
4. The application will process the image and provide an AI-generated description

## Project Structure

- `main.py` - Main application entry point
- `screenshot_tool.py` - Handles screen capture functionality
- `gemini_client.py` - Integration with Google's Gemini AI
- `hotkey_manager.py` - Manages global hotkey functionality
- `ocr_processor.py` - Handles OCR processing
- `ui_analyzer.py` - UI element analysis
- `cv_element_selector.py` - Computer vision-based element selection
- `chat_ui.py` - Chat interface implementation

## Dependencies

- pynput - For hotkey management
- Pillow - For image processing
- mss - For screen capture
- google-generativeai - For Gemini AI integration
- python-dotenv - For environment variable management
- pytesseract - For OCR functionality
- customtkinter - For enhanced UI
- pywinauto - For Windows UI automation
- opencv-python - For computer vision features

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for providing the AI capabilities
- All the open-source libraries that made this project possible 