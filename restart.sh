#!/bin/bash
pgrep -af run.sh | awk '{print $1}' | xargs kill -9
rm -f backend/rpg_database.db
cd backend && ./run.sh > backend.log 2>&1 &
