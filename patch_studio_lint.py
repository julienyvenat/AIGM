with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

content = content.replace("useState<any[]>([]);", "useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any")
content = content.replace("const [gameSystems, setGameSystems] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any", "const [gameSystems, setGameSystems] = useState<GameSystem[]>([]);")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
