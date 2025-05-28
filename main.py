from hotkey_manager import HotkeyManager
from screenshot_tool import ScreenshotTool
from gemini_client import GeminiClient
from PIL import Image
import sys

# Global instances
screenshot_handler = ScreenshotTool()
hotkey_listener = HotkeyManager()
gemini_processor = None

def trigger_screenshot_flow():
    global gemini_processor
    if not gemini_processor:
        print("Error: Gemini client is not initialized. Cannot process screenshot.")
        return

    print("Hotkey detected! Starting screenshot capture...")
    selected_image = screenshot_handler.capture_and_select()

    if selected_image:
        print(f"Region selected! Image size: {selected_image.size}")
        try:
            prompt = "Describe what you see in this screenshot in detail."
            print(f"Sending screenshot to Gemini with prompt: '{prompt}'")
            description = gemini_processor.generate_text_from_image(selected_image, prompt=prompt)

            if description:
                print("\n--- Gemini Response ---")
                print(description)
                print("-----------------------")
            else:
                print("\nFailed to get a description from Gemini.")

        except Exception as e:
            print(f"Error processing image with Gemini or saving: {e}")
    else:
        print("Screenshot selection was cancelled or failed.")

def main():
    global gemini_processor
    print("Point and Prompt Tool - Running")

    try:
        gemini_processor = GeminiClient()
    except ValueError as ve:
        print(f"Critical Error: Failed to initialize Gemini Client: {ve}")
        print("Please ensure your GOOGLE_API_KEY is set correctly in the .env file.")
        sys.exit(1)
    except Exception as e:
        print(f"Critical Error: An unexpected error occurred during Gemini Client initialization: {e}")
        sys.exit(1)

    print("Press ` + Left Mouse Click to capture a screen region.")
    print("Press Ctrl+C in the terminal to exit.")
    
    hotkey_listener.start_listening(hotkey_action=trigger_screenshot_flow)

    print("Hotkey listener stopped. Exiting application.")

if __name__ == "__main__":
    main() 