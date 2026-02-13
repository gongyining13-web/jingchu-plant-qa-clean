# src/api/langchain_qa.py（修改版）
import os
from typing import List, Optional
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

class LangChainPlantQA:
    ALIAS_MAP = {
        "菊花":"菊", "梅花":"梅", "兰花":"兰", "竹子":"竹",
        "荷花":"荷", "莲花":"荷", "桂花":"桂", "牡丹花":"牡丹",
        "杜鹃花":"杜鹃", "水仙花":"水仙", "艾草":"艾", "菖蒲叶":"菖蒲"
    }

    def __init__(self):
        # 先初始化 LLM，不管 Neo4j 是否连接成功
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama3-8b-8192"
        )
        self.graph = None  # 先设为 None
        self.neo4j_connected = False

        # 只有当所有 Neo4j 配置都存在时，才尝试连接
        if all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
            try:
                from langchain_neo4j import Neo4jGraph
                self.graph = Neo4jGraph(
                    url=NEO4J_URI,
                    username=NEO4J_USER,
                    password=NEO4J_PASSWORD
                )
                self.neo4j_connected = True
                print("✅ Neo4j 连接成功")
            except Exception as e:
                print(f"⚠️ Neo4j 连接失败：{e}，将使用离线模式")

    def get_all_plants(self) -> List[str]:
        if self.neo4j_connected:
            query = "MATCH (p:Plant) RETURN p.name AS name"
            result = self.graph.query(query)
            return [row["name"] for row in result]
        else:
            # 离线模式返回示例数据
            return ["梅花", "菊花", "兰花", "竹子"]

    def get_plant_detail(self, plant_name: str) -> Optional[dict]:
        if self.neo4j_connected:
            query = """
            MATCH (p:Plant {name: $name})
            OPTIONAL MATCH (p)-[:HAS_FAMILY]->(f:Family)
            OPTIONAL MATCH (p)-[:ASSOCIATED_WITH]->(fe:Festival)
            RETURN p.name AS name, p.latin AS latin, 
                   p.cultural_symbol AS cultural_symbol, 
                   p.distribution AS distribution,
                   f.name AS family,
                   collect(DISTINCT fe.name) AS festivals
            """
            result = self.graph.query(query, {"name": plant_name})
            if result:
                return result[0]
        # 离线模式返回示例数据
        return {
            "name": plant_name,
            "latin": "Prunus mume",
            "cultural_symbol": "高洁、坚韧",
            "distribution": "长江流域",
            "family": "蔷薇科",
            "festivals": ["春节"]
        }

    def answer_question(self, question: str) -> str:
        if self.neo4j_connected:
            # 完整的检索增强问答逻辑
            context = self.graph.query(f"MATCH (p:Plant) WHERE p.name CONTAINS '{question}' RETURN p")
            prompt = f"根据以下植物知识回答问题：{context}\n问题：{question}"
        else:
            prompt = f"请回答关于荆楚植物的问题：{question}"
        
        response = self.llm.invoke(prompt)
        return response.content