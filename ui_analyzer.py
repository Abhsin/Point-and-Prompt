import time
import threading
import tkinter as tk
from pywinauto import Desktop
from pynput import mouse, keyboard

class UIElementSelector:
    def __init__(self, highlight_color='#00FF00', highlight_width=3):
        self.highlight_color = highlight_color
        self.highlight_width = highlight_width
        self.selected_bbox = None
        self.selected_element = None
        self.overlay = None
        self.running = False
        self.listener_thread = None
        self._stop_event = threading.Event()

    def _draw_overlay(self, bbox):
        if self.overlay:
            self.overlay.destroy()
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        self.overlay = tk.Tk()
        self.overlay.overrideredirect(True)
        self.overlay.attributes('-topmost', True)
        self.overlay.attributes('-alpha', 0.3)
        self.overlay.geometry(f"{width}x{height}+{left}+{top}")
        canvas = tk.Canvas(self.overlay, width=width, height=height, highlightthickness=0, bg='')
        canvas.pack(fill='both', expand=True)
        canvas.create_rectangle(
            self.highlight_width//2, self.highlight_width//2,
            width-self.highlight_width//2, height-self.highlight_width//2,
            outline=self.highlight_color, width=self.highlight_width
        )
        self.overlay.update()

    def _remove_overlay(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

    def _find_smallest_element_at_point(self, x, y):
        elem = Desktop(backend="uia").from_point(x, y)
        smallest = elem
        try:
            while True:
                children = smallest.children()
                found = False
                for child in children:
                    rect = child.rectangle()
                    if rect.left <= x <= rect.right and rect.top <= y <= rect.bottom:
                        smallest = child
                        found = True
                        break
                if not found:
                    break
        except Exception:
            pass
        return smallest

    def _track_mouse_and_highlight(self):
        last_bbox = None
        while not self._stop_event.is_set():
            try:
                x, y = self._get_mouse_position()
                elem = self._find_smallest_element_at_point(x, y)
                rect = elem.rectangle()
                bbox = (rect.left, rect.top, rect.right, rect.bottom)
                if bbox != last_bbox:
                    self._draw_overlay(bbox)
                    last_bbox = bbox
                time.sleep(0.05)
            except Exception:
                self._remove_overlay()
                time.sleep(0.1)

    def _get_mouse_position(self):
        try:
            import win32api
            return win32api.GetCursorPos()
        except ImportError:
            # Fallback to tkinter if pywin32 is not available
            root = tk.Tk()
            root.withdraw()
            x = root.winfo_pointerx()
            y = root.winfo_pointery()
            root.destroy()
            return (x, y)

    def _on_click(self, x, y, button, pressed):
        if pressed and self._alt_pressed:
            try:
                elem = self._find_smallest_element_at_point(x, y)
                rect = elem.rectangle()
                self.selected_bbox = (rect.left, rect.top, rect.right, rect.bottom)
                self.selected_element = elem
                self._stop_event.set()
                return False  # Stop listener
            except Exception:
                pass
        return True

    def _on_press(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_gr or key == keyboard.Key.alt:
            self._alt_pressed = True

    def _on_release(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_gr or key == keyboard.Key.alt:
            self._alt_pressed = False

    def select_ui_element_with_overlay(self):
        self.selected_bbox = None
        self.selected_element = None
        self._alt_pressed = False
        self._stop_event.clear()
        self.running = True
        print("Hover over a UI element and press Alt + Left Click to select it.")
        # Start mouse/keyboard listeners
        mouse_listener = mouse.Listener(on_click=self._on_click)
        keyboard_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        mouse_listener.start()
        keyboard_listener.start()
        # Start overlay/highlight thread
        self.listener_thread = threading.Thread(target=self._track_mouse_and_highlight, daemon=True)
        self.listener_thread.start()
        # Wait for selection
        while not self._stop_event.is_set():
            time.sleep(0.05)
        self._remove_overlay()
        mouse_listener.stop()
        keyboard_listener.stop()
        self.running = False
        print(f"Selected element: {self.selected_element}")
        print(f"Bounding box: {self.selected_bbox}")
        return self.selected_element, self.selected_bbox

if __name__ == '__main__':
    selector = UIElementSelector()
    elem, bbox = selector.select_ui_element_with_overlay()
    print("\n--- Selection Result ---")
    print(f"Element: {elem}")
    print(f"Bounding Box: {bbox}")
    print("------------------------") 