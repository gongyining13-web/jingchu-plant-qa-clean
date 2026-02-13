import os
from typing import List, Optional
from langchain_neo4j import Neo4jGraph
from langchain_groq import ChatGroq
from neo4j import GraphDatabase
from dotenv import load_dotenv  # 新增：加载.env文件

# 加载本地.env文件中的环境变量（本地运行用）
load_dotenv()

# 从环境变量读取配置（优先读系统环境变量，本地读.env，云端读Streamlit Secrets）
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")  # 缺省值
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")                # 缺省值
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")    # 缺省值

class LangChainPlantQA:
    ALIAS_MAP = {
        "菊花":"菊","梅花":"梅","兰花":"兰","竹子":"竹",
        "荷花":"荷","莲花":"荷","桂花":"桂","牡丹花":"牡丹",
        "杜鹃花":"杜鹃","水仙花":"水仙","艾草":"艾","菖蒲叶":"菖蒲"
    }

    def __init__(self):
        self.graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD,
            database="neo4j",
            refresh_schema=False
        )
        self.graph.schema = """
节点：Plant(植物),Family(科),Symbol(象征),Medicinal(药用),Literature(文献),Festival(节日)
关系：BELONGS_TO_FAMILY,HAS_SYMBOL,HAS_MEDICINAL,RECORDED_IN,RELATED_TO_FESTIVAL
"""
        # 校验API Key是否存在
        if not GROQ_API_KEY:
            raise ValueError("请设置GROQ_API_KEY环境变量（本地创建.env，云端配置Secrets）")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=GROQ_API_KEY
        )
        self.plant_names = self._get_all_plants()

    def _get_all_plants(self) -> List[str]:
        res = self.graph.query("MATCH (p:Plant) RETURN p.name AS name ORDER BY p.name")
        return [r["name"] for r in res if r.get("name")]

    def _get_plant(self, question):
        for a,r in self.ALIAS_MAP.items():
            if a in question:
                return r
        for p in self.plant_names:
            if p in question:
                return p
        return None

    def answer(self, question):
        plant = self._get_plant(question)
        cypher = ""
        ans = ""

        if "文化象征" in question and plant:
            cypher = f'MATCH (p:Plant {{name:"{plant}"}}) RETURN p.cultural_symbol AS ans'
            data = self.graph.query(cypher)
            ans = data[0]["ans"] if data and data[0]["ans"] else "暂无信息"
            ans = f"{plant} 的文化象征：{ans}"

        elif "药用" in question and plant:
            cypher = f'MATCH (p:Plant {{name:"{plant}"}})-[:HAS_MEDICINAL]->(m) RETURN m.effect AS ans'
            data = self.graph.query(cypher)
            ans = data[0]["ans"] if data else "暂无药用信息"
            ans = f"{plant} 药用价值：{ans}"

        elif "端午" in question and plant:
            cypher = f'MATCH (p:Plant {{name:"{plant}"}}) RETURN p.folk_use AS ans'
            data = self.graph.query(cypher)
            ans = data[0]["ans"] if data else "暂无信息"
            ans = f"{plant} 端午用途：{ans}"

        elif "水生" in question:
            cypher = 'MATCH (p:Plant) WHERE p.distribution CONTAINS "湖北" AND p.ecological_meaning CONTAINS "水生" RETURN p.name'
            data = self.graph.query(cypher)
            if data:
                plant_names = [d["p.name"] for d in data]
                ans = "、".join(plant_names)
            else:
                ans = "无"
            ans = f"湖北水生植物：{ans}"

        else:
            ans = "请提问：文化象征、药用、端午、水生植物等"

        # 字符串拼接避免引号冲突
        final_output = "**Cypher：**\n"
        final_output += "```cypher\n"
        final_output += cypher + "\n"
        final_output += "```\n"
        final_output += "**结果：**\n"
        final_output += ans
        return final_output

    def get_plant_detail(self, plant_name):
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as s:
            r = s.run("""
                MATCH (p:Plant{name:$name})
                OPTIONAL MATCH (p)-[:HAS_SYMBOL]->(s)
                OPTIONAL MATCH (p)-[:HAS_MEDICINAL]->(m)
                OPTIONAL MATCH (p)-[:RECORDED_IN]->(l)
                OPTIONAL MATCH (p)-[:RELATED_TO_FESTIVAL]->(f)
                RETURN p.name,p.latin_name,p.family,p.genus,p.distribution,
                       p.folk_use,p.ecological_meaning,p.cultural_symbol,
                       collect(DISTINCT s.meaning) as sym,
                       collect(DISTINCT m.effect) as med,
                       collect(DISTINCT l.name) as lit,
                       collect(DISTINCT f.name) as fest
            """, name=plant_name).single()
        driver.close()
        if not r:
            return None
        return {
            "name": r["p.name"],
            "latin": r["p.latin_name"],
            "family": r["p.family"],
            "genus": r["p.genus"],
            "distribution": r["p.distribution"] or "无",
            "folk_use": r["p.folk_use"] or "无",
            "ecological": r["p.ecological_meaning"] or "无",
            "cultural_symbol": r["p.cultural_symbol"] or "无",
            "symbols": [x for x in r["sym"] if x],
            "medicinal": [x for x in r["med"] if x],
            "literature": [x for x in r["lit"] if x],
            "festivals": [x for x in r["fest"] if x]
        }