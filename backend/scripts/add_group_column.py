"""检查并添加 watchlist.group_id 列（create_all 不会 ALTER 已有表）。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text, inspect

insp = inspect(engine)
cols = [c['name'] for c in insp.get_columns('watchlist')]
print('watchlist columns:', cols)

if 'group_id' not in cols:
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE watchlist ADD COLUMN group_id INTEGER'))
        conn.commit()
    print('Added group_id column')
else:
    print('group_id already exists')
