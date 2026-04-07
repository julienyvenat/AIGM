import re

with open('backend/src/auth/router.py', 'r') as f:
    content = f.read()

# Add the import
import_str = "from fastapi.security import OAuth2PasswordRequestForm\n"
if "OAuth2PasswordRequestForm" not in content:
    content = content.replace(
        "from pydantic import BaseModel",
        "from fastapi.security import OAuth2PasswordRequestForm\nfrom pydantic import BaseModel"
    )

# Replace the login route signature
content = content.replace(
    "async def login(user_data: UserCreate, session: AsyncSession = Depends(get_session)):",
    "async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):"
)

# Replace user_data references with form_data inside login
# Note: we only want to replace inside the login function, but user_data is also used in register.
# Let's do it carefully with regex or string replacement just for the login block.

# Find the start of the login function
login_start = content.find("async def login")
login_content = content[login_start:]
modified_login = login_content.replace("user_data.username", "form_data.username").replace("user_data.password", "form_data.password")
content = content[:login_start] + modified_login

with open('backend/src/auth/router.py', 'w') as f:
    f.write(content)
