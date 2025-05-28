import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import cv2
from mss import mss

class CVElementSelector:
    def __init__(self):
        self.click_x = None
        self.click_y = None
        self.selected_bbox = None
        self.screenshot_pil = None

    def _on_click(self, event):
        self.click_x = event.x
        self.click_y = event.y
        self.root.quit()

    def _find_smallest_containing_bbox(self, pil_image, x, y):
        img = np.array(pil_image.convert('RGB'))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 30, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = float('inf')
        best_bbox = None
        for cnt in contours:
            x1, y1, w, h = cv2.boundingRect(cnt)
            if x1 <= x <= x1 + w and y1 <= y <= y1 + h and w > 10 and h > 10:
                area = w * h
                if area < min_area:
                    min_area = area
                    best_bbox = (x1, y1, x1 + w, y1 + h)
        return best_bbox

    def select_element(self):
        # Take screenshot
        with mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            self.screenshot_pil = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb, 'raw', 'BGR')
        # Show overlay and get click
        if tk._default_root is not None:
            self.root = tk.Toplevel(tk._default_root)
        else:
            self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.7)
        self.root.attributes('-topmost', True)
        tk_img = ImageTk.PhotoImage(self.screenshot_pil)
        canvas = tk.Canvas(self.root, width=self.screenshot_pil.width, height=self.screenshot_pil.height, highlightthickness=0)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        canvas.bind('<Button-1>', self._on_click)
        self.root.mainloop()
        self.root.destroy()
        # Find smallest containing rectangle
        if self.click_x is not None and self.click_y is not None:
            bbox = self._find_smallest_containing_bbox(self.screenshot_pil, self.click_x, self.click_y)
            self.selected_bbox = bbox
            # Optionally, show the detected box for confirmation
            if bbox:
                self._show_bbox_overlay(bbox)
            return self.screenshot_pil, bbox
        return self.screenshot_pil, None

    def _show_bbox_overlay(self, bbox):
        left, top, right, bottom = bbox
        if tk._default_root is not None:
            root = tk.Toplevel(tk._default_root)
        else:
            root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.7)
        root.attributes('-topmost', True)
        tk_img = ImageTk.PhotoImage(self.screenshot_pil)
        canvas = tk.Canvas(root, width=self.screenshot_pil.width, height=self.screenshot_pil.height, highlightthickness=0)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        canvas.create_rectangle(left, top, right, bottom, outline='red', width=3)
        def close(event=None):
            root.quit()
            root.destroy()
        root.bind('<Button-1>', close)
        root.after(1200, close)  # Auto-close after 1.2 seconds
        root.mainloop()

    def manual_select_region(self):
        # Take screenshot
        with mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            self.screenshot_pil = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb, 'raw', 'BGR')
        # Show overlay and let user drag to select
        if tk._default_root is not None:
            root = tk.Toplevel(tk._default_root)
        else:
            root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.7)
        root.attributes('-topmost', True)
        tk_img = ImageTk.PhotoImage(self.screenshot_pil)
        canvas = tk.Canvas(root, width=self.screenshot_pil.width, height=self.screenshot_pil.height, highlightthickness=0)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        rect = [None]
        start = [None, None]
        end = [None, None]
        def on_press(event):
            start[0], start[1] = event.x, event.y
            if rect[0]:
                canvas.delete(rect[0])
            rect[0] = None
        def on_drag(event):
            if rect[0]:
                canvas.delete(rect[0])
            rect[0] = canvas.create_rectangle(start[0], start[1], event.x, event.y, outline='red', width=3)
        def on_release(event):
            end[0], end[1] = event.x, event.y
            root.quit()
        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        root.mainloop()
        root.destroy()
        x1, y1 = start
        x2, y2 = end
        if None not in (x1, y1, x2, y2) and abs(x2-x1) > 5 and abs(y2-y1) > 5:
            left, top, right, bottom = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
            bbox = (left, top, right, bottom)
            cropped = self.screenshot_pil.crop(bbox)
            return cropped, bbox
        return None, None

if __name__ == '__main__':
    selector = CVElementSelector()
    img, bbox = selector.select_element()
    print("\n--- CV Element Selection Result ---")
    print(f"Bounding Box: {bbox}")
    print("------------------------") 