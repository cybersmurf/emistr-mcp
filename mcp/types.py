from typing import Any

class Tool:
    def __init__(self, name: str, description: str = "", inputSchema: Any = None):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }

class TextContent:
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text

class ImageContent:
    pass

class EmbeddedResource:
    pass
