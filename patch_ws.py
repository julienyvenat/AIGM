import re

with open('frontend/src/hooks/useGameWebSocket.ts', 'r') as f:
    content = f.read()

search_sig = """export function useGameWebSocket(playerId: string | null) {"""
replace_sig = """export function useGameWebSocket(playerId: string | null, onStatsUpdate?: (character: any) => void) {"""

content = content.replace(search_sig, replace_sig)

search_msg = """          if (data.type === 'scene_image' && data.url) {"""
replace_msg = """          if (data.type === 'stats_update' && data.character) {
            if (onStatsUpdate) {
              onStatsUpdate(data.character);
            }
            return;
          }

          if (data.type === 'scene_image' && data.url) {"""

content = content.replace(search_msg, replace_msg)

with open('frontend/src/hooks/useGameWebSocket.ts', 'w') as f:
    f.write(content)
