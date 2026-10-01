import os
import sys

def check_file(path):
    return os.path.exists(path)

def audit():
    print("========================================")
    print("AI-BUG-HUNTER PROJECT AUDIT")
    print("========================================\n")

    files = {
        "Documentation": "README.md",
        "Architecture": "docs/architecture/architecture.md",
        "Security Model": "docs/SECURITY_MODEL.md",
        "Installation": "docs/INSTALLATION.md",
        "Demo Script": "scripts/demo/run_demo.py",
        "Case Study": "docs/CASE_STUDY.md",
        "LinkedIn Content": "docs/LINKEDIN_POST.md"
    }

    all_passed = True
    for name, path in files.items():
        if check_file(path):
            print(f"{name}: PASS")
        else:
            print(f"{name}: FAIL ({path} not found)")
            all_passed = False

    # Check for obvious secrets in demo script
    print("Secret Scan: ", end="")
    try:
        with open("scripts/demo/run_demo.py", "r") as f:
            content = f.read().lower()
            if "api_key=" in content or "password=" in content:
                print("FAIL (Potential secret found)")
                all_passed = False
            else:
                print("PASS")
    except Exception as e:
        print(f"FAIL ({e})")
        all_passed = False

    # Demo safety check
    print("Demo Safety Check: ", end="")
    try:
        with open("scripts/demo/run_demo.py", "r") as f:
            content = f.read()
            if "127.0.0.1" in content and "google.com" not in content and "example.com" not in content:
                print("PASS")
            else:
                print("FAIL (External target or local assertion missing)")
                all_passed = False
    except Exception as e:
        print(f"FAIL ({e})")
        all_passed = False

    print("\nFinal: ", end="")
    if all_passed:
        print("READY FOR PORTFOLIO")
        sys.exit(0)
    else:
        print("NOT READY")
        sys.exit(1)

if __name__ == "__main__":
    audit()
