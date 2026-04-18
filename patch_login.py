with open("frontend/src/pages/Login.tsx", "r") as f:
    content = f.read()

# Add id to inputs so getByLabelText works
content = content.replace('type="text"', 'id="username" type="text"')
content = content.replace('type="password"', 'id="password" type="password"')

content = content.replace('<label className="block text-sm font-medium text-gray-300 mb-2">', '<label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">', 1)
content = content.replace('<label className="block text-sm font-medium text-gray-300 mb-2">', '<label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">', 1)

with open("frontend/src/pages/Login.tsx", "w") as f:
    f.write(content)
