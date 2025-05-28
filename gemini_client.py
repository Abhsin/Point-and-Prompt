import google.generativeai as genai
from PIL import Image
import os
import io
from dotenv import load_dotenv

class GeminiClient:
    def __init__(self, api_key=None):
        """
        Initializes the Gemini client.
        API key is ideally read from the .env file or GOOGLE_API_KEY environment variable if not provided.
        """
        load_dotenv()
        
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("Gemini API key not provided or found in GOOGLE_API_KEY environment variable.")
            
        genai.configure(api_key=api_key)
        # Initialize the model. For image tasks, 'gemini-pro-vision' is typically used.
        # self.model = genai.GenerativeModel('gemini-pro-vision') # Deprecated
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("Gemini client initialized with model: gemini-1.5-flash-latest")

    def generate_text_from_image(self, image_pil: Image.Image, prompt: str = "Describe this image"):
        """
        Sends an image and a prompt to the Gemini API and returns the text response.

        Args:
            image_pil: A PIL (Pillow) Image object.
            prompt: The text prompt to send along with the image.

        Returns:
            The generated text from Gemini, or None if an error occurs.
        """
        if not isinstance(image_pil, Image.Image):
            raise ValueError("Invalid image_pil argument. Expected a PIL Image object.")

        print(f"Sending image (mode: {image_pil.mode}, size: {image_pil.size}) and prompt to Gemini: '{prompt}'")
        
        try:
            # The API expects the image as bytes.
            # We convert the PIL image to bytes. Let's assume JPEG for now.
            # Note: Gemini API directly accepts PIL Image objects.
            
            response = self.model.generate_content([prompt, image_pil])
            
            if response and response.text:
                print("Received response from Gemini.")
                return response.text
            else:
                print("Received no text in response from Gemini or response was empty.")
                # You might want to inspect response.prompt_feedback here for safety ratings etc.
                if response.prompt_feedback:
                    print(f"Prompt Feedback: {response.prompt_feedback}")
                return None
        except Exception as e:
            print(f"Error generating text from image with Gemini: {e}")
            # You might want to inspect the exception type for more specific handling
            # e.g., genai.types.BlockedPromptException, genai.types.generation_types.StopCandidateException
            return None

if __name__ == '__main__':
    print("Testing GeminiClient...")
    # To test this, you need to have a GOOGLE_API_KEY environment variable set.
    # And an image file named 'test_image.png' in the same directory.
    
    # Create a dummy image for testing if 'test_image.png' doesn't exist
    try:
        test_img = Image.open("captured_region.png") # Try to load a previously captured image
        print("Loaded 'captured_region.png' for testing.")
    except FileNotFoundError:
        try:
            print("captured_region.png not found. Trying to load 'test_image.png'.")
            test_img = Image.open("test_image.png")
            print("Loaded 'test_image.png' for testing.")
        except FileNotFoundError:
            print("'test_image.png' not found. Creating a dummy image for testing.")
            test_img = Image.new('RGB', (100, 100), color = 'red')
            test_img.save("test_image.png")
            print("Created and saved 'test_image.png' (100x100 red square).")

    try:
        client = GeminiClient() # API key from env
        description = client.generate_text_from_image(test_img, prompt="What is in this image?")
        
        if description:
            print("\n--- Gemini Response ---")
            print(description)
            print("-----------------------")
        else:
            print("\nFailed to get a description from Gemini.")
            
    except ValueError as ve:
        print(f"Initialization Error: {ve}")
        print("Please ensure your GOOGLE_API_KEY environment variable is set correctly.")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}") 