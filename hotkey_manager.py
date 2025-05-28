from pynput import keyboard, mouse

class HotkeyManager:
    def __init__(self):
        self.keyboard_listener = None
        self.mouse_listener = None
        self.grave_pressed = False
        self.active_hotkey_action = None

    def on_press(self, key):
        try:
            if key == keyboard.KeyCode.from_char('`'):
                self.grave_pressed = True
        except AttributeError:
            pass # Ignore special keys like shift, ctrl, etc. for this check

    def on_release(self, key):
        try:
            if key == keyboard.KeyCode.from_char('`'):
                self.grave_pressed = False
        except AttributeError:
            pass

    def on_click(self, x, y, button, pressed):
        if pressed and self.grave_pressed and button == mouse.Button.left:
            print("Hotkey (Grave + Left Click) detected!")
            if self.active_hotkey_action:
                self.active_hotkey_action()

    def start_listening(self, hotkey_action=None):
        self.active_hotkey_action = hotkey_action
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.keyboard_listener.start()

        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self.on_click
        )
        self.mouse_listener.start()
        
        print("Hotkey listener started. Press ` + Left Click.")
        # Keep the listeners running
        self.keyboard_listener.join()
        self.mouse_listener.join()

    def stop_listening(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        print("Hotkey listener stopped.")

if __name__ == '__main__':
    manager = HotkeyManager()
    
    def my_action():
        print("My custom hotkey action was triggered!")

    manager.start_listening(hotkey_action=my_action)
    # In a real application, you'd have a loop or event system here.
    # For this test, we'll just stop it after a while if needed,
    # or let it run until manually stopped (Ctrl+C).
    # For simplicity, this example will run until Ctrl+C. 