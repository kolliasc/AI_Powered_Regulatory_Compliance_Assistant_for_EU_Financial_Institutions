import sys
import os

project_root = "/Workspace/Users/christoforosmav20@gmail.com/bundle/ai-regulatory-assistant/files"

if os.path.exists(project_root):
    if project_root not in sys.path:
        sys.path.append(project_root)
    print(f" Path successfully matched! Linked to: {project_root}")
else:
    print(f" Path check failed. Could not find: {project_root}")

# Azure OpenAI environment variables so Pydantic can validate them
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://accenture2026ab.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "4dn2Hd4qnFDuPpLTQX17BSXQc8EZ92j2IQUSmmFEv4fejDIW9VypJQQJ99CFAC5T7U2XJ3w3AAABACOGwAeF"
os.environ["AZURE_OPENAI_API_VERSION"] = "2024-12-01-preview"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4.1"

from src.config.settings import settings
print("Settings loaded perfectly!")