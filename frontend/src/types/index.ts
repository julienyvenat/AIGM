export interface GameSystem {
  id: string;
  name: string;
  description: string;
  rules_summary: string;
  dice_system: string;
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
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  level: number;
  experience: number;
  known_spells: Record<string, unknown>[];
  spell_slots: Record<string, unknown>;
  class_resources: Record<string, unknown>;
  inventory?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any
}
