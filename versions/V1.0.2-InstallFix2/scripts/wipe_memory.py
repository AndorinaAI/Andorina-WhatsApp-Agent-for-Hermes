import urllib.request

collections = ["user_memory", "system_memory", "hermes_memory", "andorina_memory"]

print("🧠 Starting memory wipe...")

for c in collections:
    url = f"http://localhost:6333/collections/{c}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req) as r:
            print(f"✅ Collection '{c}' deleted.")
    except Exception as e:
        print(f"ℹ️ Collection '{c}' not found or already empty.")

print("\n✨ Memory wipe finished.")
