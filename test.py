import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

with open('instagram_comments.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
# print(str(data).encode("cp1252", errors="ignore").decode("cp1252"))
for entry in data:
    print(entry["comment"])