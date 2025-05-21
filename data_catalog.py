import os
import json
import streamlit as st

class DataCatalog:
    def __init__(self):
        self.entries = []

    def link_directory(self, root_path: str, recursive: bool = True):
        """Link a directory and iterate over its files."""
        for dirpath, dirnames, filenames in os.walk(root_path):
            for file in filenames:
                full_path = os.path.join(dirpath, file)
                self.entries.append({
                    "type": "file",
                    "path": full_path,
                    "extension": os.path.splitext(file)[1],
                    "comment": ""
                })
            if not recursive:
                break

    def list_entries(self):
        """Print a list of all entries."""
        for entry in self.entries:
            print(f"[{entry['type']}] {entry['path']} ({entry['extension']})")

    def add_comment(self, path: str, comment: str):
        """Add or update a comment for a given file path."""
        for entry in self.entries:
            if entry["path"] == path:
                entry["comment"] = comment
                return True
        return False

    def export_to_json(self, filepath: str):
        """Export the catalog to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.entries, f, indent=2)

def display_directory_level(current_path, root_path):
    try:
        entries = sorted(os.listdir(current_path))
    except PermissionError:
        st.write("[Permission Denied]")
        return

    st.markdown("### Directory: " + current_path)

    if current_path != root_path:
        parent_path = os.path.dirname(current_path)
        if st.button("⬅️ Go Back"):
            st.session_state["current_path"] = parent_path
            st.query_params["reload"] = "1"

    for entry in entries:
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            if st.button(f"📁 {entry}", key=full_path):
                st.session_state["current_path"] = full_path
                st.query_params["reload"] = "1"
        else:
            st.write(f"📄 {entry}")

# Streamlit UI
if __name__ == "__main__":
    st.title("Data Catalog Directory Browser")
    root_path = st.text_input("Enter the root directory path:", value=r"C:\\Users\\jdvdb\\OneDrive\\Documenten")

    if "current_path" not in st.session_state:
        st.session_state["current_path"] = root_path

    if os.path.isdir(st.session_state["current_path"]):
        display_directory_level(st.session_state["current_path"], root_path)