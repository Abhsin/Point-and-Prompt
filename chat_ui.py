import customtkinter as ctk
from PIL import Image #, ImageTk # ImageTk might not be needed if using CTkImage exclusively
import tkinter as tk # For constants like WORD, END, if not re-exported by ctk
from screenshot_tool import ScreenshotTool
from ui_analyzer import UIElementSelector
from ocr_processor import extract_text_from_image
import multiprocessing
from cv_element_selector import CVElementSelector
from gemini_client import GeminiClient

def run_selector(queue):
    from ui_analyzer import UIElementSelector
    selector = UIElementSelector()
    elem, bbox = selector.select_ui_element_with_overlay()
    # Only send bbox (element is not picklable)
    queue.put((bbox, getattr(elem, 'window_text', lambda: "")( )))

class ChatWindow(ctk.CTk):
    def __init__(self, gemini_client_instance, initial_image: Image.Image = None, initial_description: str = None):
        super().__init__()

        self.gemini_client = gemini_client_instance
        self.current_image_pil = initial_image # Store the PIL image
        self.last_ocr_text = None
        self.screenshot_tool = ScreenshotTool()
        self.ui_selector = UIElementSelector()
        self.tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update if needed

        self.title("Point & Prompt Chat")
        self.geometry("900x800")

        ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

        # Top button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=(10,0), sticky="ew")
        self.button_frame.grid_columnconfigure((0,1,2,3), weight=1)

        # Remove Freeform button
        # self.freeform_btn = ctk.CTkButton(self.button_frame, text="Freeform Region", command=self.select_freeform)
        # self.freeform_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.context_btn = ctk.CTkButton(self.button_frame, text="Context-Aware Element", command=self.select_context_aware)
        self.context_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.ocr_btn = ctk.CTkButton(self.button_frame, text="OCR Only", command=self.run_ocr_on_current)
        self.ocr_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.cv_btn = ctk.CTkButton(self.button_frame, text="CV Element Select", command=self.select_cv_element)
        self.cv_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.manual_btn = ctk.CTkButton(self.button_frame, text="Freeform Select", command=self.select_manual)
        self.manual_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Main content layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2) # Text/Chat area wider
        self.grid_rowconfigure(1, weight=1)    # Image and Chat history take most space
        self.grid_rowconfigure(2, weight=0)    # Input and send button fixed size

        # === Image Display ===
        self.image_label = ctk.CTkLabel(self, text="Screenshot will appear here", width=300, height=300)
        self.image_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        if self.current_image_pil:
            self.display_image(self.current_image_pil)

        # === Chat History ===
        self.chat_history_textbox = ctk.CTkTextbox(self, wrap="word", state="disabled") # Use string values
        self.chat_history_textbox.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Configure tags for chat messages
        self.chat_history_textbox.tag_config("user_tag_main", justify='right', foreground="#4a90e2")
        self.chat_history_textbox.tag_config("user_tag_prefix", justify='right', foreground="#4a90e2")
        self.chat_history_textbox.tag_config("gemini_tag_main", justify='left', foreground="#50C878")
        self.chat_history_textbox.tag_config("gemini_tag_prefix", justify='left', foreground="#50C878")

        if initial_description:
            self.add_message_to_chat("Gemini", initial_description)

        # === User Input ===
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.user_input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message...")
        self.user_input_entry.grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        self.user_input_entry.bind("<Return>", self.send_message_on_enter)

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(5,0), pady=5, sticky="ew")
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing) # Handle window close

    def display_image(self, pil_image: Image.Image):
        if not pil_image:
            self.image_label.configure(image=None, text="No image loaded")
            return

        img_width, img_height = pil_image.size
        label_width = 300 # Target display width for the image in the UI
        label_height = 300 # Target display height for the image in the UI

        # Calculate aspect ratio to fit within the label dimensions
        # This logic is for CTkImage which takes size parameter for display size
        # The actual image isn't resized here, CTkImage handles scaling.
        
        # Create CTkImage
        # The size parameter in CTkImage is the display size, not a resize of the original image.
        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(label_width, label_height))
        
        self.image_label.configure(image=ctk_image, text="")
        # self.image_label.image = ctk_image # CTkImage does not need this explicit reference for GC like PhotoImage

    def add_message_to_chat(self, sender: str, message: str):
        self.chat_history_textbox.configure(state="normal")
        prefix = f"{sender}: "
        full_message = f"{message}\n\n"
        if sender == "You":
            self.chat_history_textbox.insert(tk.END, prefix, "user_tag_prefix")
            self.chat_history_textbox.insert(tk.END, full_message, "user_tag_main")
        else: # Gemini or System
            self.chat_history_textbox.insert(tk.END, prefix, "gemini_tag_prefix")
            self.chat_history_textbox.insert(tk.END, full_message, "gemini_tag_main")
        self.chat_history_textbox.configure(state="disabled")
        self.chat_history_textbox.see(tk.END)

    def send_message_on_enter(self, event):
        self.send_message()

    def send_message(self):
        user_text = self.user_input_entry.get()
        if not user_text.strip():
            return # Don't send empty messages

        self.add_message_to_chat("You", user_text)
        self.user_input_entry.delete(0, tk.END) # tk.END is fine here

        if not self.current_image_pil:
            self.add_message_to_chat("System", "Error: No image is loaded to chat about.")
            return
        
        if not self.gemini_client:
            self.add_message_to_chat("System", "Error: Gemini client not available.")
            return

        # Send to Gemini (image and the new user_text as prompt)
        # For a conversational context, you might need to send the history or adapt the prompt.
        # For now, we send the image and the latest user query.
        self.send_button.configure(state="disabled")
        self.user_input_entry.configure(state="disabled")
        
        # In a real app, you'd run this in a separate thread to avoid UI freeze
        # For simplicity, running it directly here.
        try:
            # Gemini Vision models can take a list of [prompt, image, prompt, image ...]
            # or [prompt, image]
            # To make it conversational with an image, the prompt should reference the image implicitly.
            # The user's text becomes the new prompt.
            print(f"Sending to Gemini: Image + User Prompt: '{user_text}'")
            gemini_response = self.gemini_client.generate_text_from_image(self.current_image_pil, prompt=user_text)
            if gemini_response:
                self.add_message_to_chat("Gemini", gemini_response)
            else:
                self.add_message_to_chat("Gemini", "Sorry, I couldn't get a response.")
        except Exception as e:
            self.add_message_to_chat("System", f"Error communicating with Gemini: {e}")
        finally:
            self.send_button.configure(state="normal")
            self.user_input_entry.configure(state="normal")
            
    def select_context_aware(self):
        self.add_message_to_chat("System", "[Context-Aware] Hover and press Alt+Left Click on a UI element...")
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=run_selector, args=(queue,))
        p.start()
        bbox, elem_text = queue.get()  # This will block until selection is made
        p.join()
        if bbox:
            from mss import mss
            with mss() as sct:
                monitor = {"left": bbox[0], "top": bbox[1], "width": bbox[2]-bbox[0], "height": bbox[3]-bbox[1]}
                sct_img = sct.grab(monitor)
                img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb, 'raw', 'BGR')
                self.current_image_pil = img
                self.display_image(img)
                self.add_message_to_chat("System", f"Context-aware element captured: {elem_text}")
                # Run OCR
                self.add_message_to_chat("System", "Running OCR on selected element...")
                text = extract_text_from_image(img, tesseract_path=self.tesseract_path)
                self.last_ocr_text = text
                if text:
                    self.add_message_to_chat("OCR", text)
                else:
                    self.add_message_to_chat("OCR", "No text detected.")
                # Send to Gemini with OCR context
                if self.gemini_client:
                    self.add_message_to_chat("System", "Sending image and OCR to Gemini for description...")
                    try:
                        prompt = f"Describe this image. The detected text in the image is: {text if text else '[No text detected]'}"
                        desc = self.gemini_client.generate_text_from_image(img, prompt=prompt)
                        if desc:
                            self.add_message_to_chat("Gemini", desc)
                        else:
                            self.add_message_to_chat("Gemini", "No response from Gemini.")
                    except Exception as e:
                        self.add_message_to_chat("Gemini", f"Error: {e}")
        else:
            self.add_message_to_chat("System", "Context-aware selection cancelled or failed.")

    def run_ocr_on_current(self):
        if not self.current_image_pil:
            self.add_message_to_chat("System", "No image loaded for OCR.")
            return
        self.add_message_to_chat("System", "Running OCR on current image...")
        text = extract_text_from_image(self.current_image_pil, tesseract_path=self.tesseract_path)
        self.last_ocr_text = text
        if text:
            self.add_message_to_chat("OCR", text)
        else:
            self.add_message_to_chat("OCR", "No text detected.")

    def select_cv_element(self):
        self.add_message_to_chat("System", "[CV] Click on a UI element in the overlay...")
        selector = CVElementSelector()
        img, bbox = selector.select_element()
        if bbox:
            self.current_image_pil = img.crop(bbox)
            self.display_image(self.current_image_pil)
            self.add_message_to_chat("System", f"CV element selected: {bbox}")
            # Run OCR
            self.add_message_to_chat("System", "Running OCR on selected element...")
            text = extract_text_from_image(self.current_image_pil, tesseract_path=self.tesseract_path)
            self.last_ocr_text = text
            if text:
                self.add_message_to_chat("OCR", text)
            else:
                self.add_message_to_chat("OCR", "No text detected.")
            # Send to Gemini with OCR context
            if self.gemini_client:
                self.add_message_to_chat("System", "Sending image and OCR to Gemini for description...")
                try:
                    prompt = f"Describe this image. The detected text in the image is: {text if text else '[No text detected]'}"
                    desc = self.gemini_client.generate_text_from_image(self.current_image_pil, prompt=prompt)
                    if desc:
                        self.add_message_to_chat("Gemini", desc)
                    else:
                        self.add_message_to_chat("Gemini", "No response from Gemini.")
                except Exception as e:
                    self.add_message_to_chat("Gemini", f"Error: {e}")
        else:
            self.add_message_to_chat("System", "CV element selection cancelled or failed.")

    def select_manual(self):
        self.add_message_to_chat("System", "[Manual] Click and drag to select a region...")
        selector = CVElementSelector()
        img, bbox = selector.manual_select_region()
        if img and bbox:
            self.current_image_pil = img
            self.display_image(self.current_image_pil)
            self.add_message_to_chat("System", f"Manual region selected: {bbox}")
            # Run OCR
            self.add_message_to_chat("System", "Running OCR on selected region...")
            text = extract_text_from_image(self.current_image_pil, tesseract_path=self.tesseract_path)
            self.last_ocr_text = text
            if text:
                self.add_message_to_chat("OCR", text)
            else:
                self.add_message_to_chat("OCR", "No text detected.")
            # Send to Gemini with OCR context
            if self.gemini_client:
                self.add_message_to_chat("System", "Sending image and OCR to Gemini for description...")
                try:
                    prompt = f"Describe this image. The detected text in the image is: {text if text else '[No text detected]'}"
                    desc = self.gemini_client.generate_text_from_image(self.current_image_pil, prompt=prompt)
                    if desc:
                        self.add_message_to_chat("Gemini", desc)
                    else:
                        self.add_message_to_chat("Gemini", "No response from Gemini.")
                except Exception as e:
                    self.add_message_to_chat("Gemini", f"Error: {e}")
        else:
            self.add_message_to_chat("System", "Manual selection cancelled or failed.")

    def _on_closing(self):
        print("Chat window closed by user.")
        # Potentially stop hotkey listener or other cleanup if this is the main interaction window
        self.destroy() # Close the customtkinter window
        # If main.py is waiting for this window, it should now continue or exit.
        # For now, this just closes the window. The hotkey listener in main.py continues.


if __name__ == '__main__':
    from gemini_client import GeminiClient
    print("Running chat_ui.py with real GeminiClient...")
    try:
        test_img = Image.open("captured_region.png")
        print("Loaded 'captured_region.png' for UI test.")
    except FileNotFoundError:
        try:
            test_img = Image.open("test_image.png")
            print("Loaded 'test_image.png' for UI test.")
        except FileNotFoundError:
            print("No test image found, creating a dummy one.")
            test_img = Image.new('RGB', (300, 200), color = 'blue')
            test_img.save("test_image.png")
    gemini_client = GeminiClient()
    initial_desc = "Welcome! Select a region to get started."
    app = ChatWindow(gemini_client_instance=gemini_client, initial_image=test_img, initial_description=initial_desc)
    app.mainloop()
    print("chat_ui.py finished.") 