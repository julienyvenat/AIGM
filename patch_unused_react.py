import re

files_to_fix = [
    'frontend/src/components/CharacterModal.tsx',
    'frontend/src/components/CharacterSidePanel.tsx'
]

for file_path in files_to_fix:
    with open(file_path, 'r') as f:
        content = f.read()

    # Remove unused React import
    content = content.replace("import React from 'react';\n", "")
    content = content.replace("import React, { useState } from 'react';\n", "import { useState } from 'react';\n")

    with open(file_path, 'w') as f:
        f.write(content)
