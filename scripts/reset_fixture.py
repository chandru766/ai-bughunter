import os

print("Resetting Local Vulnerable Lab...")
db_path = "fixtures/vulnerable_api/fixture.db"
if os.path.exists(db_path):
    os.remove(db_path)
print("Account A (user-a) and Account B (user-b) are ready for testing.")
