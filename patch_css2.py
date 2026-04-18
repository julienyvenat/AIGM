with open("frontend/src/index.css", "r") as f:
    content = f.read()

content = content.replace('@import "tailwindcss";', '@import "tailwindcss";\n@plugin "@tailwindcss/typography";')

with open("frontend/src/index.css", "w") as f:
    f.write(content)
