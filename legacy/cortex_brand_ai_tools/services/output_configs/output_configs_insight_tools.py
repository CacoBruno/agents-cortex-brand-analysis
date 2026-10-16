OUTPUT_CONFIG = {
    "insights": {
        "final_paths": [
            ["insights"],
        ],
        "file_paths": [],
    },
    "whatsapp": {
        "final_paths": [
            ["whatsapp_message", "output", "final_text"],
            ["whatsapp_message"],
            ["insights"],
        ],
        "file_paths": [],
    },
    "meeting_script": {
        "final_paths": [
            ["meeting_script"],
            ["meeting_insights", "meeting_script", "llm_output"],
            ["meeting_insights"],
            ["insights"],
        ],
        "file_paths": [
            ["meeting_insights", "files"],
        ],
    },
}