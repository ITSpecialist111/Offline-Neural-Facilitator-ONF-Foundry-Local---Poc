import pyautogui
import os
from datetime import datetime

class VisionService:
    def __init__(self, export_dir=None):
        if not export_dir:
            user_profile = os.environ.get('USERPROFILE')
            if user_profile:
                self.export_dir = os.path.join(user_profile, 'Documents', 'FacilitatorReports', 'Evidence')
            else:
                self.export_dir = "evidence"
        else:
            self.export_dir = export_dir

        os.makedirs(self.export_dir, exist_ok=True)

    def capture_screen(self):
        """
        Captures the screen and saves it to the evidence directory.
        Returns the absolute filepath.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return filepath
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
