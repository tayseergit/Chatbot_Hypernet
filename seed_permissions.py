import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend_service.core.services.permission_service import PermissionService

if __name__ == "__main__":
    print("Running seed_defaults...")
    svc = PermissionService()
    inserted = svc.seed_defaults()
    print(f"Seed completed. Inserted {inserted} new permissions.")
