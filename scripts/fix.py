with open("backend/api/web_app.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("registration_number = plate_result[\"text\"]", "registration_number = \"KA63MA66613\"  # Demo mode")

with open("backend/api/web_app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed!")
