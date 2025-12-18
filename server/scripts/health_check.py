import sys
import os
import importlib

def check_file(path):
    if os.path.exists(path):
        print(f"[OK] File found: {path}")
        return True
    else:
        print(f"[ERROR] File missing: {path}")
        return False

def check_module(module_name):
    try:
        importlib.import_module(module_name)
        print(f"[OK] Module imported: {module_name}")
        return True
    except ImportError as e:
        print(f"[ERROR] Module missing: {module_name} ({e})")
        return False
    except Exception as e:
        print(f"[ERROR] Module error: {module_name} ({e})")
        return False

def main():
    print("=== Eliza Client Health Check ===")
    
    # 1. Environment
    print(f"Python Version: {sys.version}")
    
    # 2. Dependencies
    required_modules = ['PyQt5', 'requests']
    for mod in required_modules:
        check_module(mod)
        
    # 3. File Integrity
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    critical_files = [
        "client/main.py",
        "client/ui/main_window.py",
        "client/ui/components.py",
        "client/ui/styles.py",
        "config/settings.json"
    ]
    
    for f in critical_files:
        check_file(os.path.join(project_root, f))
        
    # 4. Code Integrity (Try to import client modules)
    sys.path.append(project_root)
    try:
        print("Checking Client UI Modules...")
        from client.ui.components import TacticalButton
        # Check if critical method exists (Prevention of recent bug)
        if not hasattr(TacticalButton, 'set_accent_color'):
             print("[ERROR] TacticalButton missing 'set_accent_color' method!")
        else:
             print("[OK] TacticalButton integrity check passed.")
             
        import client.ui.main_window
        print("[OK] MainWindow module loaded successfully.")
        
    except Exception as e:
        print(f"[CRITICAL] Code Integrity Check Failed: {e}")
        
    print("=== Check Complete ===")

if __name__ == "__main__":
    main()
