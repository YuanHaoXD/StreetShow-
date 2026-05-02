import base64
import json
import requests

API_URL = "https://poloai.top/v1beta/models/gemini-3-pro-image-preview:generateContent"
API_KEY = "sk-qeB57n8bPjtYqKxyZ4sFw7MUMy4Uu9bbv0HAsPHH3AFKd8OH"  # 替换为真实 token

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

base64_image1 = encode_image("cloth.jpg")
base64_image2 = encode_image("model.jpg")

payload = {
    "contents": [
        {
            "role": "user",
            "parts": [
                {"text": "将衣服换上模特"},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image1}},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image2}},
            ],
        }
    ],
    "generationConfig": {"imageConfig": {"aspectRatio": "1:1", "imageSize": "4K"}},
    "safetySettings": [
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ],
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "PoloAPI/1.0.0 (https://poloai.top)",
    "Content-Type": "application/json",
}

response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
print(response.text)
