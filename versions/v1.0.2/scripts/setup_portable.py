#!/usr/bin/env python3
import os, sys, shutil, subprocess, tarfile, urllib.request
from pathlib import Path

# Paths (Dynamic detection)
SKILL_DIR  = Path(__file__).parent.parent.absolute()
BIN_DIR    = SKILL_DIR / "bin"
QDRANT_BIN = BIN_DIR / "qdrant"

QDRANT_URL = "https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-musl.tar.gz"

def setup_qdrant():
    print("🔍 Checking Qdrant...")
    
    # 1. Check if already in PATH
    if shutil.which("qdrant"):
        print("✅ Qdrant is already installed in the system.")
        return True

    # 2. Check if already in our bin folder
    if QDRANT_BIN.exists():
        print(f"✅ Qdrant found in {QDRANT_BIN}")
        return True

    # 3. Download if missing
    print("🚀 Qdrant not found. Downloading portable version...")
    try:
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        tar_path = BIN_DIR / "qdrant.tar.gz"
        
        print(f"📥 Downloading from GitHub...")
        urllib.request.urlretrieve(QDRANT_URL, tar_path)
        
        print("📦 Extracting...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=BIN_DIR)
        
        # Cleanup
        tar_path.unlink()
        
        # The binary is usually named 'qdrant' inside the tar
        # Let's ensure it's executable
        if QDRANT_BIN.exists():
            QDRANT_BIN.chmod(0o755)
            print("✅ Qdrant installed successfully in skill folder.")
            return True
        else:
            print("❌ Extraction failed: binary not found.")
            return False
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False

if __name__ == "__main__":
    if setup_qdrant():
        sys.exit(0)
    else:
        sys.exit(1)
