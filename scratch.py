import re

message_text = "+44 74 5567 8820"
clean_text = re.sub(r'[\s\-]', '', message_text)
phone_match = re.search(r'(\+964|0)?7\d{9}\b', clean_text) or re.search(r'\+?\d{10,15}\b', clean_text)

print(f"Message: {message_text}")
print(f"Clean: {clean_text}")
print(f"Match: {phone_match.group(0) if phone_match else None}")
