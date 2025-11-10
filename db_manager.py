"""
Database Manager - DuckDB Storage for Annotations
High-performance alternative to JSONL files
"""
import duckdb
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class AnnotationDatabase:
    """Manages annotation storage in DuckDB"""
    
    def __init__(self, db_path: str = "annotations.duckdb"):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Create database and tables if they don't exist"""
        self.conn = duckdb.connect(self.db_path)
        
        # Create tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id VARCHAR PRIMARY KEY,
                file_name VARCHAR,
                doc_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_sentences_id START 1;
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sentences (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_sentences_id'),
                doc_id VARCHAR,
                sent_idx INTEGER,
                tokens VARCHAR[]
            )
        """)
        
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_entities_id START 1;
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_entities_id'),
                doc_id VARCHAR,
                sent_idx INTEGER,
                start_idx INTEGER,
                end_idx INTEGER,
                entity_type VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_relations_id START 1;
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY DEFAULT nextval('seq_relations_id'),
                doc_id VARCHAR,
                sent_idx INTEGER,
                src_start INTEGER,
                src_end INTEGER,
                tgt_start INTEGER,
                tgt_end INTEGER,
                relation_type VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indices for fast queries
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_doc ON entities(doc_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_relations_doc ON relations(doc_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sentences_doc ON sentences(doc_id, sent_idx)")
        
        self.conn.commit()
    
    def import_from_jsonl(self, jsonl_path: str, progress_callback=None) -> int:
        """Import documents from JSONL file"""
        if not os.path.exists(jsonl_path):
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        file_name = os.path.basename(jsonl_path)
        documents_imported = 0
        
        # First pass - count total lines for progress
        total_lines = 0
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    total_lines += 1
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue
                
                try:
                    doc = json.loads(line)
                    doc_id = doc.get('doc_id', f'doc_{idx}')
                    
                    # Insert document
                    self.conn.execute("""
                        INSERT OR REPLACE INTO documents (doc_id, file_name, doc_index)
                        VALUES (?, ?, ?)
                    """, (doc_id, file_name, idx))
                    
                    # Insert sentences
                    sentences = doc.get('sentences', [])
                    for sent_idx, tokens in enumerate(sentences):
                        self.conn.execute("""
                            INSERT INTO sentences (doc_id, sent_idx, tokens)
                            VALUES (?, ?, ?)
                        """, (doc_id, sent_idx, tokens))
                    
                    # Insert entities
                    ner = doc.get('ner', [])
                    for sent_idx, sent_entities in enumerate(ner):
                        for entity in sent_entities:
                            if len(entity) >= 3:
                                self.conn.execute("""
                                    INSERT INTO entities (doc_id, sent_idx, start_idx, end_idx, entity_type)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (doc_id, sent_idx, entity[0], entity[1], entity[2]))
                    
                    # Insert relations
                    relations = doc.get('relations', [])
                    for sent_idx, sent_relations in enumerate(relations):
                        for relation in sent_relations:
                            if len(relation) >= 5:
                                self.conn.execute("""
                                    INSERT INTO relations (doc_id, sent_idx, src_start, src_end, 
                                                         tgt_start, tgt_end, relation_type)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (doc_id, sent_idx, relation[0], relation[1], 
                                     relation[2], relation[3], relation[4]))
                    
                    documents_imported += 1
                    
                    # Call progress callback every document
                    if progress_callback and total_lines > 0:
                        progress = 0.3 + (documents_imported / total_lines) * 0.3  # 30% to 60%
                        progress_callback(progress, f"Importing document {documents_imported}/{total_lines}")
                    
                except Exception as e:
                    print(f"Error importing document {idx}: {e}")
                    continue
        
        self.conn.commit()
        return documents_imported
    
    def export_to_jsonl(self, output_path: str) -> int:
        """Export all documents to JSONL file"""
        documents = self.get_all_documents()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        
        return len(documents)
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        result = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()
        return result[0] if result else 0
    
    def get_document_ids(self) -> List[str]:
        """Get all document IDs in order"""
        result = self.conn.execute("""
            SELECT doc_id FROM documents 
            ORDER BY doc_index
        """).fetchall()
        return [row[0] for row in result]
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a single document with all its data"""
        # Get document info
        doc_info = self.conn.execute("""
            SELECT doc_id FROM documents WHERE doc_id = ?
        """, (doc_id,)).fetchone()
        
        if not doc_info:
            return None
        
        # Get sentences
        sentences_result = self.conn.execute("""
            SELECT tokens FROM sentences 
            WHERE doc_id = ? 
            ORDER BY sent_idx
        """, (doc_id,)).fetchall()
        sentences = [list(row[0]) for row in sentences_result]
        
        # Get entities grouped by sentence
        entities_result = self.conn.execute("""
            SELECT sent_idx, start_idx, end_idx, entity_type 
            FROM entities 
            WHERE doc_id = ?
            ORDER BY sent_idx, start_idx
        """, (doc_id,)).fetchall()
        
        # Group entities by sentence
        max_sent = len(sentences)
        ner = [[] for _ in range(max_sent)]
        for sent_idx, start, end, etype in entities_result:
            if sent_idx < max_sent:
                ner[sent_idx].append([start, end, etype])
        
        # Get relations grouped by sentence
        relations_result = self.conn.execute("""
            SELECT sent_idx, src_start, src_end, tgt_start, tgt_end, relation_type
            FROM relations
            WHERE doc_id = ?
            ORDER BY sent_idx
        """, (doc_id,)).fetchall()
        
        # Group relations by sentence
        relations = [[] for _ in range(max_sent)]
        for sent_idx, src_start, src_end, tgt_start, tgt_end, rtype in relations_result:
            if sent_idx < max_sent:
                relations[sent_idx].append([src_start, src_end, tgt_start, tgt_end, rtype])
        
        return {
            'doc_id': doc_id,
            'sentences': sentences,
            'ner': ner,
            'relations': relations
        }
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents (WARNING: Can be slow for large databases)"""
        doc_ids = self.get_document_ids()
        return [self.get_document(doc_id) for doc_id in doc_ids]
    
    def save_document(self, doc: Dict, event_pump_callback=None) -> bool:
        """Save or update a document"""
        try:
            doc_id = doc.get('doc_id', 'unknown')
            
            # Delete existing data for this document
            self.conn.execute("DELETE FROM sentences WHERE doc_id = ?", (doc_id,))
            self.conn.execute("DELETE FROM entities WHERE doc_id = ?", (doc_id,))
            self.conn.execute("DELETE FROM relations WHERE doc_id = ?", (doc_id,))
            
            # Keep UI responsive
            if event_pump_callback:
                event_pump_callback()
            
            # Update document timestamp
            self.conn.execute("""
                UPDATE documents 
                SET modified_at = CURRENT_TIMESTAMP 
                WHERE doc_id = ?
            """, (doc_id,))
            
            # Batch insert sentences
            sentences = doc.get('sentences', [])
            if sentences:
                sentence_data = [(doc_id, sent_idx, tokens) for sent_idx, tokens in enumerate(sentences)]
                self.conn.executemany("""
                    INSERT INTO sentences (doc_id, sent_idx, tokens)
                    VALUES (?, ?, ?)
                """, sentence_data)
                
                # Keep UI responsive
                if event_pump_callback:
                    event_pump_callback()
            
            # Batch insert entities
            ner = doc.get('ner', [])
            entity_data = []
            for sent_idx, sent_entities in enumerate(ner):
                for entity in sent_entities:
                    if len(entity) >= 3:
                        entity_data.append((doc_id, sent_idx, entity[0], entity[1], entity[2]))
            
            if entity_data:
                self.conn.executemany("""
                    INSERT INTO entities (doc_id, sent_idx, start_idx, end_idx, entity_type)
                    VALUES (?, ?, ?, ?, ?)
                """, entity_data)
                
                # Keep UI responsive
                if event_pump_callback:
                    event_pump_callback()
            
            # Batch insert relations
            relations = doc.get('relations', [])
            relation_data = []
            for sent_idx, sent_relations in enumerate(relations):
                for relation in sent_relations:
                    if len(relation) >= 5:
                        relation_data.append((doc_id, sent_idx, relation[0], relation[1],
                                            relation[2], relation[3], relation[4]))
            
            if relation_data:
                self.conn.executemany("""
                    INSERT INTO relations (doc_id, sent_idx, src_start, src_end,
                                         tgt_start, tgt_end, relation_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, relation_data)
                
                # Keep UI responsive
                if event_pump_callback:
                    event_pump_callback()
            
            self.conn.commit()
            
            # Final pump after commit
            if event_pump_callback:
                event_pump_callback()
            return True
            
        except Exception as e:
            print(f"Error saving document: {e}")
            self.conn.rollback()
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its data"""
        try:
            self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            self.conn.rollback()
            return False
    
    def search_entities(self, entity_type: Optional[str] = None, 
                       search_text: Optional[str] = None) -> List[Dict]:
        """Search for entities across all documents"""
        query = "SELECT DISTINCT doc_id, entity_type FROM entities WHERE 1=1"
        params = []
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        
        if search_text:
            query += " AND entity_type LIKE ?"
            params.append(f"%{search_text}%")
        
        result = self.conn.execute(query, params).fetchall()
        return [{'doc_id': row[0], 'entity_type': row[1]} for row in result]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        stats['total_documents'] = self.conn.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]
        
        stats['total_entities'] = self.conn.execute(
            "SELECT COUNT(*) FROM entities"
        ).fetchone()[0]
        
        stats['total_relations'] = self.conn.execute(
            "SELECT COUNT(*) FROM relations"
        ).fetchone()[0]
        
        stats['entity_types'] = self.conn.execute("""
            SELECT entity_type, COUNT(*) as count 
            FROM entities 
            GROUP BY entity_type 
            ORDER BY count DESC
        """).fetchall()
        
        stats['relation_types'] = self.conn.execute("""
            SELECT relation_type, COUNT(*) as count 
            FROM relations 
            GROUP BY relation_type 
            ORDER BY count DESC
        """).fetchall()
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Utility functions for migration
def migrate_jsonl_to_db(jsonl_path: str, db_path: str = "annotations.duckdb") -> Tuple[bool, str]:
    """Migrate a JSONL file to DuckDB"""
    try:
        db = AnnotationDatabase(db_path)
        count = db.import_from_jsonl(jsonl_path)
        db.close()
        return True, f"Successfully imported {count} documents"
    except Exception as e:
        return False, f"Migration failed: {e}"


def export_db_to_jsonl(db_path: str, output_path: str) -> Tuple[bool, str]:
    """Export DuckDB to JSONL file"""
    try:
        db = AnnotationDatabase(db_path)
        count = db.export_to_jsonl(output_path)
        db.close()
        return True, f"Successfully exported {count} documents"
    except Exception as e:
        return False, f"Export failed: {e}"

