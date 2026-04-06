import re
from pathlib import Path

def apply_fixes(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    # Generic fix for blank lines and trailing whitespace
    content = re.sub(r'([ \t]+)$', '', content, flags=re.MULTILINE)

    with open(file_path, "w") as f:
        f.write(content)

apply_fixes("backend/src/auth/router.py")
apply_fixes("backend/src/auth/utils.py")
apply_fixes("backend/src/engine/models.py")
apply_fixes("backend/tests/test_auth.py")
