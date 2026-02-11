import requests
import os
import time

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "eliza-client-key-12345"
HEADERS = {"X-API-Key": API_KEY}

def test_file_listing():
    print("Testing File Listing...")
    # Ensure a dummy file exists
    os.makedirs("server/output", exist_ok=True)
    with open("server/output/test_doc.txt", "w") as f:
        f.write("Hello World")
        
    try:
        response = requests.get(f"{BASE_URL}/files/output", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            files = data.get("files", [])
            print(f"Files found: {len(files)}")
            found = False
            for f in files:
                print(f" - {f['name']} ({f['url']})")
                if f['name'] == "test_doc.txt":
                    found = True
            
            if found:
                print("PASS: test_doc.txt found in list")
            else:
                print("FAIL: test_doc.txt not found")
        else:
            print(f"FAIL: Status {response.status_code} - {response.text}")
    except Exception as e:
        print(f"FAIL: Connection error {e}")

def test_project_template():
    print("\nTesting Project Template...")
    try:
        payload = {
            "name": "Template Test Project",
            "template": "software_team"
        }
        response = requests.post(f"{BASE_URL}/projects/", json=payload, headers=HEADERS)
        if response.status_code == 200:
            pid = response.json().get("project_id")
            print(f"Project Created: {pid}")
            
            # Verify agents were created
            time.sleep(1) # Wait for DB
            resp_agents = requests.get(f"{BASE_URL}/projects/{pid}/agents", headers=HEADERS)
            agents = resp_agents.json().get("agents", [])
            print(f"Agents created: {len(agents)}")
            roles = [a['role_name'] for a in agents]
            print(f"Roles: {roles}")
            
            if "Product Manager" in roles and "Coder" in roles:
                print("PASS: Template agents created")
            else:
                print("FAIL: Template agents missing")
        else:
            print(f"FAIL: Status {response.status_code} - {response.text}")
    except Exception as e:
        print(f"FAIL: Connection error {e}")

if __name__ == "__main__":
    test_file_listing()
    test_project_template()
