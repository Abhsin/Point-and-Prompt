import tkinter as tk
from PIL import Image, ImageTk
import mss

class ScreenshotTool:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.selection_coords = None
        self.screenshot_pil = None

    def _on_mouse_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = None

    def _on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        if self.rect:
            self.canvas.delete(self.rect)
        
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, cur_x, cur_y, 
            outline='red', width=2
        )

    def _on_mouse_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        # Ensure start coordinates are top-left and end coordinates are bottom-right
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # Check if the selection is valid (has some area)
        if x2 - x1 > 0 and y2 - y1 > 0:
            self.selection_coords = (int(x1), int(y1), int(x2), int(y2))
        else:
            print("Invalid selection. Please try again.")
            self.selection_coords = None # Reset if selection is invalid
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = None
            return # Don't close window if selection is tiny/invalid
        
        if self.root:
            self.root.quit() # Quit the mainloop
            self.root.destroy() # Destroy the window
            self.root = None

    def capture_and_select(self):
        self.selection_coords = None # Reset previous selection
        try:
            with mss.mss() as sct:
                # monitor = sct.monitors[0] # All monitors, includes virtual screen for selection
                if len(sct.monitors) > 1:
                    monitor_number = 1 # Typically the primary monitor
                    print(f"Attempting to capture primary monitor: {sct.monitors[monitor_number]}")
                    monitor = sct.monitors[monitor_number]
                else:
                    print("Only one monitor detected (or virtual screen). Using monitor 0.")
                    monitor = sct.monitors[0]
                
                sct_img = sct.grab(monitor)
                self.screenshot_pil = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb, 'raw', 'BGR')

            # Use Toplevel if a root window exists, otherwise Tk
            if tk._default_root is not None:
                self.root = tk.Toplevel(tk._default_root)
            else:
                self.root = tk.Tk()
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-alpha", 0.3) # Semi-transparent overlay
            self.root.attributes("-topmost", True)
            self.root.wait_visibility(self.root)
            self.root.wm_attributes('-alpha', 0.3)

            # Prepare Tkinter photo image
            tk_image = ImageTk.PhotoImage(self.screenshot_pil)
            
            self.canvas = tk.Canvas(self.root, width=self.screenshot_pil.width, height=self.screenshot_pil.height, highlightthickness=0)
            self.canvas.pack()
            self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

            self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
            self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
            self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
            
            # Add a way to cancel selection
            self.root.bind("<Escape>", lambda e: self._cancel_selection())

            print("Overlay active. Click and drag to select. Press Esc to cancel.")
            self.root.mainloop()

            if self.selection_coords and self.screenshot_pil:
                # Ensure coordinates are within image bounds
                x1, y1, x2, y2 = self.selection_coords
                img_width, img_height = self.screenshot_pil.size
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(img_width, x2)
                y2 = min(img_height, y2)
                if x1 < x2 and y1 < y2: # Check again after clamping
                    cropped_image = self.screenshot_pil.crop((x1, y1, x2, y2))
                    return cropped_image
                else:
                    print("Selection coordinates out of bounds or invalid after clamping.")
                    return None
            return None

        except Exception as e:
            print(f"Error during screen capture or selection: {e}")
            if self.root:
                try:
                    self.root.destroy()
                except tk.TclError:
                    pass # In case it's already destroyed or in a bad state
                self.root = None
            return None
        finally:
            # Ensure any Tkinter window is destroyed if an error occurred mid-process
            if self.root:
                try:
                    self.root.destroy()
                except tk.TclError:
                     pass # Window might already be gone
                self.root = None
    
    def _cancel_selection(self):
        print("Selection cancelled.")
        self.selection_coords = None
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

if __name__ == '__main__':
    tool = ScreenshotTool()
    selected_region = tool.capture_and_select()

    if selected_region:
        print(f"Selected region of size: {selected_region.size}")
        try:
            # For testing, save the image or show it
            selected_region.save("selected_screenshot.png")
            print("Selected region saved as selected_screenshot.png")
            # selected_region.show() # This might open in an external viewer
        except Exception as e:
            print(f"Error saving/showing image: {e}")
    else:
        print("No region was selected or an error occurred.") 