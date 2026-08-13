import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

modules = [
    "backend_service.core.services.session_service",
    "backend_service.core.services.message_service",
    "backend_service.core.services.context_service",
    "backend_service.core.services.authentication_service",
    "backend_service.core.services.action_log_service",
    "backend_service.core.services.permission_service",
    "backend_service.tools.tool_executor"
]

for mod in modules:
    print(f"Debug: Importing {mod}")
    try:
        __import__(mod)
    except Exception as e:
        print(f"Error importing {mod}: {e}")

print("Debug: All container imports finished")
