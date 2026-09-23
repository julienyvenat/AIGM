export interface GameSystem {
  id: string;
  name: string;
  description: string;
  rules_summary: string;
  dice_system: string;
  core_rules_prompt: string;
  character_schema: Record<string, string>;
}

export interface Universe {
  id: string;
  game_system_id: string;
  name: string;
  description: string;
  image_url: string;
  game_system?: GameSystem;
}

export interface GameSession {
  id: string;
  universe_id: string;
  status: string;
  host_id: string;
  current_battlemap_url?: string;
  game_mode: string;
  voice_enabled: boolean;
  // "AI" (default): the narrator/arbitrator agents autonomously drive the
  // session, as before. "HUMAN": host_id is the human GM -- the AI never
  // auto-narrates/auto-arbitrates, see Play.tsx's GM panel.
  gm_type: 'AI' | 'HUMAN';
  universe?: Universe;
}

export interface Character {
  id: string;
  name: string;
  universe_id: string;
  user_id: string;
  game_session_id?: string | null;
  hp: number;
  max_hp: number;
  armor_class: number;
  speed: number;
  reference_portrait_url: string | null;
  stats: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  level: number;
  experience: number;
  known_spells: Record<string, unknown>[];
  spell_slots: Record<string, unknown>;
  class_resources: Record<string, unknown>;
  inventory?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
}
