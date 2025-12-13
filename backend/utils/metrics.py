import sqlite3
from datetime import datetime, timedelta
import json
import os

class MetricsCollector:
    """Recolecta y almacena métricas del sistema"""
    
    def __init__(self, db_path='data/history.db'):
        self.db_path = db_path
        # Crear directorio data si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Crear tabla de historial si no existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS occupancy_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                count INTEGER NOT NULL,
                max_capacity INTEGER NOT NULL,
                occupancy_rate REAL,
                models_used TEXT,
                fps REAL,
                inference_time REAL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON occupancy_log(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def log_inference(self, count, models_used, inference_time, fps, max_capacity=50):
        """Guardar resultado de inferencia en DB"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO occupancy_log 
                (count, max_capacity, occupancy_rate, models_used, fps, inference_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                count,
                max_capacity,
                count / max_capacity if max_capacity > 0 else 0,
                json.dumps(models_used),
                fps,
                inference_time
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error guardando en DB: {e}")
    
    def get_history(self, start_time=None, end_time=None):
        """Obtener historial de ocupación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if start_time and end_time:
            cursor.execute('''
                SELECT timestamp, count, occupancy_rate 
                FROM occupancy_log
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time, end_time))
        else:
            # Por defecto, últimas 24 horas
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute('''
                SELECT timestamp, count, occupancy_rate 
                FROM occupancy_log
                WHERE timestamp >= ?
                ORDER BY timestamp
            ''', (yesterday.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = [
            {
                'timestamp': row[0],
                'count': row[1],
                'occupancy_rate': row[2]
            }
            for row in rows
        ]
        
        return history
    
    def get_avg_occupancy(self, start_time=None, end_time=None):
        """Calcular ocupación promedio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if start_time and end_time:
            cursor.execute('''
                SELECT AVG(occupancy_rate) 
                FROM occupancy_log
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_time, end_time))
        else:
            cursor.execute('SELECT AVG(occupancy_rate) FROM occupancy_log')
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result else 0.0
    
    def get_peak_count(self, start_time=None, end_time=None):
        """Obtener conteo máximo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if start_time and end_time:
            cursor.execute('''
                SELECT MAX(count) 
                FROM occupancy_log
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_time, end_time))
        else:
            cursor.execute('SELECT MAX(count) FROM occupancy_log')
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result else 0
    
    def get_peak_time(self, start_time=None, end_time=None):
        """Obtener timestamp del pico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if start_time and end_time:
            cursor.execute('''
                SELECT timestamp 
                FROM occupancy_log
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY count DESC
                LIMIT 1
            ''', (start_time, end_time))
        else:
            cursor.execute('''
                SELECT timestamp 
                FROM occupancy_log
                ORDER BY count DESC
                LIMIT 1
            ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
