import os
import json
import subprocess
from pathlib import Path

# -----------------------------
# 1) Configure your credentials
# -----------------------------
# Replace these with your real OnShape API credentials
os.environ["ONSHAPE_API"] = "https://cad.onshape.com"
os.environ["ONSHAPE_ACCESS_KEY"] = "VsPdiI6pfLLfU28Gqwpywy5Z"
os.environ["ONSHAPE_SECRET_KEY"] = "YaUUBHAS3BC6828W7zbLNHBnNX8NzJfJB7UcYcg0eGD5VQAv"

# -----------------------------------------
# 2) Create a project folder and config.json
# -----------------------------------------
project_dir = Path("my_onshape_robot")
project_dir.mkdir(exist_ok=True)

config = {
    # Use the full OnShape assembly URL copied from the correct assembly tab
    "url": "https://cad.onshape.com/documents/9e83762b80a69a2cde640794/w/7f8437b889dc88e43d4b4d72/e/f5bb304961cdbf8b45a0f878",
    
    # Tell onshape-to-robot to export URDF
    "output_format": "urdf"
}

config_path = project_dir / "config.json"
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

# -----------------------------------------
# 3) Run the exporter
# -----------------------------------------
# Equivalent to running:
#   onshape-to-robot my_onshape_robot
subprocess.run(
    ["onshape-to-robot", str(project_dir)],
    check=True
)

print(f"Export complete. Check the folder: {project_dir.resolve()}")