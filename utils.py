import json
import os
from config import DATA_PATH

def load_data(file_name):
    """Load JSON data from a given file safely."""
    file_path = os.path.join(DATA_PATH, file_name)  # ✅ Correct way to handle file paths

    if not os.path.exists(file_path):  # ✅ Check if file exists
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
