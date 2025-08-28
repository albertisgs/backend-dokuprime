import json
import requests
from pathlib import Path

class DifyDataset:
    def __init__(self, base_url, id, api_key):
        self.base_url = base_url
        self.id = id
        self.api_key = api_key
        print("DifyDataset Initialized")
        
    def upload_document_to_dataset(self, file_path):
        """Upload a document to a dataset using the API."""
        
        # Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        url = f"{self.base_url}/datasets/{self.id}/document/create-by-file"
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        files = {
            'file': (file_path_obj.name, open(file_path, 'rb'))
        }
        data_payload = {
            "indexing_technique": "high_quality",
            "process_rule": {
                "rules": {
                    "pre_processing_rules": [
                        {"id": "remove_extra_spaces", "enabled": False},
                        {"id": "remove_urls_emails", "enabled": False}
                    ],
                    "segmentation": {
                        "separator": "===[TEXT]===",
                        "max_tokens": 4000,
                        "chunk_overlap": 400
                    }
                },
                "mode": "custom"
            }
        }
        data = {
            'data': (None, json.dumps(data_payload), 'text/plain')
        }
        
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise
        finally:
            if 'file' in files:
                files['file'][1].close()
