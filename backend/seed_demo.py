"""Optional sample data; run only for screenshots and classroom demonstrations."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from main import DEFAULT_DB, init_database

init_database(DEFAULT_DB)
date = datetime.now(timezone.utc).isoformat(timespec="seconds")
with sqlite3.connect(DEFAULT_DB) as conn:
    count = conn.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]
    if count:
        print(f'Database already contains {count} reviews. No examples added.')
    else:
        examples = [
            ('Ana Rojas', 5, 'La atención fue excelente y encontré lo que buscaba.'),
            ('Sofía Mora', 4, 'Muy bonitas las prendas y el personal fue muy amable.'),
            ('Luis Vargas', 3, 'Me gustó la ropa, pero tardaron un poco en atenderme.'),
        ]
        conn.executemany('INSERT INTO reviews(user_name,rating,comment,published_at) VALUES(?,?,?,?)',
                         [(name,rating,comment,date) for name,rating,comment in examples])
        print('3 reseñas ficticias de ejemplo creadas.')
