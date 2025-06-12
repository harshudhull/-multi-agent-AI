import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class MemoryManager:
    """Lightweight memory management for storing context and conversation data"""
    
    def __init__(self, db_path: str = "intake_system.db"):
        self.db_path = db_path
        self._init_memory_tables()
    
    def _init_memory_tables(self):
        """Initialize memory tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_store (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store(self, key: str, data: Dict[str, Any], expires_hours: int = 24):
        """Store data in memory with optional expiration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_store (key, data, expires_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(data), expires_at))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error storing in memory: {e}")
            return False
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data, expires_at FROM memory_store 
                WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
            """, (key, datetime.now()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            print(f"Error retrieving from memory: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete data from memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM memory_store WHERE key = ?", (key,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error deleting from memory: {e}")
            return False
    
    def get_all_memory(self) -> List[Dict[str, Any]]:
        """Get all memory data (for debugging/monitoring)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, data, created_at, expires_at FROM memory_store 
                WHERE expires_at IS NULL OR expires_at > ?
                ORDER BY created_at DESC
            """, (datetime.now(),))
            
            rows = cursor.fetchall()
            memory_data = []
            
            for row in rows:
                memory_data.append({
                    "key": row[0],
                    "data": json.loads(row[1]),
                    "created_at": row[2],
                    "expires_at": row[3]
                })
            
            conn.close()
            return memory_data
            
        except Exception as e:
            print(f"Error getting all memory: {e}")
            return []
    
    def cleanup_expired(self) -> int:
        """Clean up expired memory entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM memory_store 
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """, (datetime.now(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up expired memory: {e}")
            return 0
    
    def store_conversation(self, conversation_id: str, message_type: str, 
                         content: str, metadata: Dict[str, Any] = None):
        """Store conversation history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            message_id = f"{conversation_id}_{datetime.now().timestamp()}"
            
            cursor.execute("""
                INSERT INTO conversation_history 
                (id, conversation_id, message_type, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, conversation_id, message_type, content, 
                  json.dumps(metadata) if metadata else None))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error storing conversation: {e}")
            return False
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT message_type, content, metadata, created_at 
                FROM conversation_history 
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """, (conversation_id,))
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                history.append({
                    "message_type": row[0],
                    "content": row[1],
                    "metadata": json.loads(row[2]) if row[2] else None,
                    "created_at": row[3]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count total entries
            cursor.execute("SELECT COUNT(*) FROM memory_store")
            total_entries = cursor.fetchone()[0]
            
            # Count expired entries
            cursor.execute("""
                SELECT COUNT(*) FROM memory_store 
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """, (datetime.now(),))
            expired_entries = cursor.fetchone()[0]
            
            # Count active entries
            active_entries = total_entries - expired_entries
            
            conn.close()
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "cleanup_needed": expired_entries > 0
            }
            
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {}