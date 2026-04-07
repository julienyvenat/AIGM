with open('frontend/src/context/AuthContext.tsx', 'r') as f:
    content = f.read()

old_error_handling = """    if (!response.ok) {
      throw new Error('Login failed');
    }"""

new_error_handling = """    if (!response.ok) {
      const errorData = await response.json();
      console.error("Détails de l'erreur 422 :", errorData);
      throw new Error('Login failed');
    }"""

content = content.replace(old_error_handling, new_error_handling)

with open('frontend/src/context/AuthContext.tsx', 'w') as f:
    f.write(content)
