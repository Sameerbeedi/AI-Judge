"""
Neo4j Graph Database Service
Handles relationships between cases, arguments, and legal precedents
"""
from neo4j import GraphDatabase
import os
from typing import List, Dict, Optional

class Neo4jService:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def create_case_node(self, case_id: str):
        """Create a case node in the graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Case {case_id: $case_id})
                SET c.created_at = datetime()
                RETURN c
            """, case_id=case_id)
    
    def create_argument_nodes(self, case_id: str, side_a_summary: str, side_b_summary: str):
        """Create argument nodes and link them to case"""
        with self.driver.session() as session:
            session.run("""
                MATCH (c:Case {case_id: $case_id})
                CREATE (a:Argument {
                    side: 'A',
                    summary: $side_a_summary,
                    created_at: datetime()
                })
                CREATE (b:Argument {
                    side: 'B',
                    summary: $side_b_summary,
                    created_at: datetime()
                })
                CREATE (c)-[:HAS_ARGUMENT]->(a)
                CREATE (c)-[:HAS_ARGUMENT]->(b)
                CREATE (a)-[:OPPOSES]->(b)
                CREATE (b)-[:OPPOSES]->(a)
            """, case_id=case_id, side_a_summary=side_a_summary, side_b_summary=side_b_summary)
    
    def create_verdict_node(self, case_id: str, verdict_summary: str, winning_side: str):
        """Create verdict node and link to case"""
        with self.driver.session() as session:
            session.run("""
                MATCH (c:Case {case_id: $case_id})
                CREATE (v:Verdict {
                    summary: $verdict_summary,
                    winning_side: $winning_side,
                    decided_at: datetime()
                })
                CREATE (c)-[:HAS_VERDICT]->(v)
            """, case_id=case_id, verdict_summary=verdict_summary, winning_side=winning_side)
    
    def add_follow_up(self, case_id: str, side: str, argument_summary: str, changed_verdict: bool):
        """Add follow-up argument to the graph"""
        with self.driver.session() as session:
            session.run("""
                MATCH (c:Case {case_id: $case_id})
                CREATE (f:FollowUp {
                    side: $side,
                    summary: $argument_summary,
                    changed_verdict: $changed_verdict,
                    created_at: datetime()
                })
                CREATE (c)-[:HAS_FOLLOWUP]->(f)
            """, case_id=case_id, side=side, argument_summary=argument_summary, changed_verdict=changed_verdict)
    
    def link_similar_cases(self, case_id_1: str, case_id_2: str, similarity_score: float):
        """Create similarity relationship between cases"""
        with self.driver.session() as session:
            session.run("""
                MATCH (c1:Case {case_id: $case_id_1})
                MATCH (c2:Case {case_id: $case_id_2})
                MERGE (c1)-[r:SIMILAR_TO]-(c2)
                SET r.score = $score, r.updated_at = datetime()
            """, case_id_1=case_id_1, case_id_2=case_id_2, score=similarity_score)
    
    def find_similar_cases(self, case_id: str, limit: int = 5) -> List[Dict]:
        """Find similar cases using graph traversal"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Case {case_id: $case_id})-[r:SIMILAR_TO]-(similar:Case)
                RETURN similar.case_id as case_id, r.score as score
                ORDER BY r.score DESC
                LIMIT $limit
            """, case_id=case_id, limit=limit)
            return [{"case_id": record["case_id"], "score": record["score"]} 
                    for record in result]
    
    def get_argument_patterns(self, winning_side: str, limit: int = 10) -> List[Dict]:
        """Find common patterns in winning arguments"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Case)-[:HAS_VERDICT]->(v:Verdict {winning_side: $winning_side})
                MATCH (c)-[:HAS_ARGUMENT]->(a:Argument {side: $winning_side})
                RETURN a.summary as argument, count(a) as frequency
                ORDER BY frequency DESC
                LIMIT $limit
            """, winning_side=winning_side, limit=limit)
            return [{"argument": record["argument"], "frequency": record["frequency"]} 
                    for record in result]
    
    def get_case_statistics(self) -> Dict:
        """Get overall statistics from the graph"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Case)
                OPTIONAL MATCH (c)-[:HAS_VERDICT]->(v:Verdict)
                OPTIONAL MATCH (c)-[:HAS_FOLLOWUP]->(f:FollowUp)
                RETURN 
                    count(DISTINCT c) as total_cases,
                    count(DISTINCT v) as decided_cases,
                    count(DISTINCT f) as total_followups,
                    count(DISTINCT CASE WHEN v.winning_side = 'A' THEN v END) as side_a_wins,
                    count(DISTINCT CASE WHEN v.winning_side = 'B' THEN v END) as side_b_wins
            """)
            record = result.single()
            return {
                "total_cases": record["total_cases"],
                "decided_cases": record["decided_cases"],
                "total_followups": record["total_followups"],
                "side_a_wins": record["side_a_wins"],
                "side_b_wins": record["side_b_wins"]
            }
    
    def check_connection(self) -> bool:
        """Check if Neo4j connection is working"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as num")
                return result.single()["num"] == 1
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            return False


# Global instance
neo4j_service = Neo4jService()
