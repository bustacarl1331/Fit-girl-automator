import json
import os
import time

HISTORY_FILE = "history.json"

class HistoryManager:
    def __init__(self):
        self.history = self.load_history()

    def load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return {}
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_or_update(self, url, path, selected_files):
        # We use URL as key
        self.history[url] = {
            "path": path,
            "selected_files": selected_files, # List of filenames or IDs
            "last_accessed": time.time()
        }
        self.save_history()

    def get_entry(self, url):
        return self.history.get(url)

    def delete_entry(self, url):
        if url in self.history:
            del self.history[url]
            self.save_history()
            return True
        return False

    def get_all_sorted(self):
        # Return list of (url, data) sorted by last_accessed desc
        items = list(self.history.items())
        items.sort(key=lambda x: x[1].get('last_accessed', 0), reverse=True)
        return items
