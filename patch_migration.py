with open("backend/alembic/versions/af2b32a164cd_feat_multiplayer_models_auth.py", "r") as f:
    content = f.read()

content = content.replace("batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])", "batch_op.create_foreign_key('fk_character_user_id', 'user', ['user_id'], ['id'])")
content = content.replace("batch_op.create_foreign_key(None, 'universe', ['universe_id'], ['id'])", "batch_op.create_foreign_key('fk_character_universe_id', 'universe', ['universe_id'], ['id'])")

content = content.replace("batch_op.drop_constraint(None, type_='foreignkey')", "batch_op.drop_constraint('fk_character_user_id', type_='foreignkey')\n        batch_op.drop_constraint('fk_character_universe_id', type_='foreignkey')")


# Ensure only one replacement happened for downgrade by removing the duplicate
import re
content = re.sub(r"        batch_op.drop_constraint\('fk_character_user_id', type_='foreignkey'\)\n        batch_op.drop_constraint\('fk_character_universe_id', type_='foreignkey'\)\n        batch_op.drop_constraint\('fk_character_user_id', type_='foreignkey'\)\n        batch_op.drop_constraint\('fk_character_universe_id', type_='foreignkey'\)", r"        batch_op.drop_constraint('fk_character_user_id', type_='foreignkey')\n        batch_op.drop_constraint('fk_character_universe_id', type_='foreignkey')", content)


with open("backend/alembic/versions/af2b32a164cd_feat_multiplayer_models_auth.py", "w") as f:
    f.write(content)
