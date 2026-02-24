#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荆楚植物文化知识图谱 - 完整问答系统
支持环境变量：NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
新增 LangChainPlantQA 类，实现自然语言到 Cypher 的智能转换（兼容 langchain 0.1.0）
"""
import os
from neo4j import GraphDatabase
import jieba
import logging
from typing import List, Optional

# ---------- LangChain 相关导入（适配 0.1.0） ----------
from langchain.chains import GraphCypherQAChain
from langchain.graphs import Neo4jGraph
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class PlantQASystem:
    # ========== 类属性：别名映射表 ==========
    ALIAS_MAP = {
        "菊花": "菊", "梅花": "梅", "兰花": "兰", "竹子": "竹",
        "荷花": "荷", "莲花": "荷", "桂花": "桂", "牡丹花": "牡丹",
        "杜鹃花": "杜鹃", "水仙花": "水仙", "艾草": "艾", "菖蒲叶": "菖蒲",
        "松树": "松", "柏树": "柏", "柳树": "柳", "桑树": "桑",
        "茶树": "茶", "桃树": "桃", "银杏树": "银杏", "梧桐树": "梧桐"
    }

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        初始化Neo4j连接
        优先级：传入参数 > 环境变量 > 本地开发默认值
        """
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "12345678")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.plant_names = self._get_all_plants()
        self._setup_jieba()
        logger.info(f"✅ 完整问答系统已启动，连接至 {self.uri}，包含 {len(self.plant_names)} 种植物")

    def _get_all_plants(self) -> List[str]:
        with self.driver.session() as session:
            result = session.run("MATCH (p:Plant) RETURN p.name as name ORDER BY p.name")
            return [record['name'] for record in result]

    def _setup_jieba(self):
        for name in self.plant_names:
            jieba.add_word(name)
        for alias in self.ALIAS_MAP.keys():
            jieba.add_word(alias)
        jieba.add_word("端午节")
        jieba.add_word("春节")
        jieba.add_word("重阳节")
        jieba.add_word("中秋节")
        jieba.add_word("清明节")

    # ---------- 核心方法 ----------
    def answer(self, question: str) -> str:
        for plant in self.plant_names:
            if plant in question:
                return self._answer_for_plant(plant, question)
        for alias, real_name in self.ALIAS_MAP.items():
            if alias in question:
                if real_name in self.plant_names:
                    return self._answer_for_plant(real_name, question)
                else:
                    return f"❌ 暂未收录该种植物（{alias}）"
        words = jieba.lcut(question)
        for word in words:
            if word in self.plant_names:
                return self._answer_for_plant(word, question)
        return self._handle_general_question(question)

    def _answer_for_plant(self, plant: str, question: str) -> str:
        q_type = self._identify_question_type(question)
        with self.driver.session() as session:
            if q_type == "symbol":
                return self._query_symbol(session, plant)
            elif q_type == "medicinal":
                return self._query_medicinal(session, plant)
            elif q_type == "distribution":
                return self._query_distribution(session, plant)
            elif q_type == "folk":
                return self._query_folk(session, plant)
            elif q_type == "festival":
                return self._query_festival(session, plant)
            elif q_type == "literature":
                return self._query_literature(session, plant)
            elif q_type == "taxonomy":
                return self._query_taxonomy(session, plant)
            else:
                return self._query_basic(session, plant)

    def _identify_question_type(self, question: str) -> str:
        q = question.lower()
        if any(k in q for k in ["象征", "寓意", "代表", "含义", "文化"]):
            return "symbol"
        elif any(k in q for k in ["药用", "功效", "药效", "治疗", "治病"]):
            return "medicinal"
        elif any(k in q for k in ["分布", "哪里", "在哪", "产地", "生长"]):
            return "distribution"
        elif any(k in q for k in ["民俗", "用途", "使用", "怎么用"]):
            return "folk"
        elif any(k in q for k in ["节日", "端午", "春节", "重阳", "中秋", "清明"]):
            return "festival"
        elif any(k in q for k in ["文献", "记载", "诗经", "楚辞", "诗词"]):
            return "literature"
        elif any(k in q for k in ["科", "属", "分类"]):
            return "taxonomy"
        else:
            return "basic"

    # ---------- 具体查询方法 ----------
    def _query_symbol(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})-[:HAS_SYMBOL]->(s:Symbol)
            RETURN collect(s.meaning) as symbols
        """, name=plant)
        record = result.single()
        if record and record['symbols']:
            return f"🌿 {plant}的文化象征：\n" + "、".join(record['symbols'])
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.cultural_symbol as symbol
        """, name=plant)
        record = result.single()
        if record and record['symbol']:
            return f"🌿 {plant}的文化象征：\n{record['symbol']}"
        return f"🌿 {plant}的文化象征信息暂缺。"

    def _query_medicinal(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})-[:HAS_MEDICINAL]->(m:Medicinal)
            RETURN collect(m.effect) as effects
        """, name=plant)
        record = result.single()
        if record and record['effects']:
            return f"💊 {plant}的药用价值：\n" + "、".join(record['effects'])
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.medicinal_value as med
        """, name=plant)
        record = result.single()
        if record and record['med'] and record['med'] != '无药用记载':
            return f"💊 {plant}的药用价值：\n{record['med']}"
        return f"💊 {plant}的药用价值信息暂缺。"

    def _query_distribution(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.distribution as dist
        """, name=plant)
        record = result.single()
        if record and record['dist']:
            return f"🗺️ {plant}的分布区域：\n{record['dist']}"
        return f"🗺️ {plant}的分布信息暂缺。"

    def _query_folk(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.folk_use as folk
        """, name=plant)
        record = result.single()
        if record and record['folk']:
            return f"🏮 {plant}的民俗用途：\n{record['folk']}"
        return f"🏮 {plant}的民俗用途信息暂缺。"

    def _query_festival(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})-[:RELATED_TO_FESTIVAL]->(f:Festival)
            RETURN collect(f.name) as festivals
        """, name=plant)
        record = result.single()
        if record and record['festivals']:
            return f"🎉 {plant}相关的节日：\n" + "、".join(record['festivals'])
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.festival as festival
        """, name=plant)
        record = result.single()
        if record and record['festival']:
            return f"🎉 {plant}相关的节日：\n{record['festival']}"
        return f"🎉 {plant}的节日信息暂缺。"

    def _query_literature(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})-[:RECORDED_IN]->(l:Literature)
            RETURN collect(l.name) as literatures
        """, name=plant)
        record = result.single()
        if record and record['literatures']:
            return f"📖 {plant}的文献记载：\n" + "、".join(record['literatures'])
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.literature_source as lit
        """, name=plant)
        record = result.single()
        if record and record['lit']:
            return f"📖 {plant}的文献出处：\n{record['lit']}"
        return f"📖 {plant}的文献信息暂缺。"

    def _query_taxonomy(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.latin_name as latin, p.family as family, p.genus as genus
        """, name=plant)
        record = result.single()
        if record:
            return f"🌱 {plant}（{record['latin']}）\n🏷️ 科：{record['family']}  属：{record['genus']}"
        return f"🌱 {plant}的科属信息暂缺。"

    def _query_basic(self, session, plant: str) -> str:
        result = session.run("""
            MATCH (p:Plant {name: $name})
            RETURN p.latin_name as latin, p.family as family, p.genus as genus,
                   p.distribution as dist, p.cultural_symbol as symbol
        """, name=plant)
        record = result.single()
        if record:
            info = f"🌿 {plant}（{record['latin']}）\n"
            info += f"🏷️ 科：{record['family']}  属：{record['genus']}\n"
            if record['dist']:
                info += f"🗺️ 分布：{record['dist']}\n"
            if record['symbol']:
                info += f"✨ 文化象征：{record['symbol']}"
            return info
        return f"🌿 {plant} 的信息暂缺。"

    # ---------- 通用问题 ----------
    def _handle_general_question(self, question: str) -> str:
        q = question.lower()
        if any(k in q for k in ["所有植物", "有哪些植物", "植物列表"]):
            plants_str = "、".join(self.plant_names)
            return f"📚 知识库中共有 {len(self.plant_names)} 种植物：\n{plants_str}"
        elif "端午" in q:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Plant)-[:RELATED_TO_FESTIVAL]->(f:Festival)
                    WHERE f.name CONTAINS '端午'
                    RETURN p.name as name
                """)
                plants = [r['name'] for r in result]
                if plants:
                    return f"🎋 端午节相关植物：{ '、'.join(plants) }"
                else:
                    return "🎋 端午节相关植物：艾、菖蒲、蒜"
        elif "春节" in q:
            return "🧧 春节相关植物：橘、桃、水仙"
        elif "重阳" in q:
            return "🏔️ 重阳节相关植物：菊、茱萸"
        elif "中秋" in q:
            return "🌕 中秋节相关植物：桂"
        elif "清明" in q:
            return "🌧️ 清明节相关植物：柳、杜鹃、柏"
        elif "楚辞" in q or "诗经" in q:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Plant)-[:RECORDED_IN]->(l:Literature)
                    WHERE l.name CONTAINS '楚辞' OR l.name CONTAINS '诗经'
                    RETURN p.name as name
                """)
                plants = [r['name'] for r in result]
                if plants:
                    return f"📜 《楚辞》《诗经》中记载的植物：{ '、'.join(plants[:10]) }……"
        return "❓ 请明确指定植物名称（如：兰有什么文化象征？）"

    # ---------- 对外接口 ----------
    def get_plant_detail(self, plant_name: str) -> dict:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Plant {name: $name})
                OPTIONAL MATCH (p)-[:HAS_SYMBOL]->(s:Symbol)
                OPTIONAL MATCH (p)-[:HAS_MEDICINAL]->(m:Medicinal)
                OPTIONAL MATCH (p)-[:RECORDED_IN]->(l:Literature)
                OPTIONAL MATCH (p)-[:RELATED_TO_FESTIVAL]->(f:Festival)
                RETURN p.name as name,
                       p.latin_name as latin_name,
                       p.family as family,
                       p.genus as genus,
                       p.distribution as distribution,
                       p.folk_use as folk_use,
                       p.ecological_meaning as ecological,
                       p.cultural_symbol as cultural_symbol,
                       collect(DISTINCT s.meaning) as symbols,
                       collect(DISTINCT m.effect) as medicinal,
                       collect(DISTINCT l.name) as literature,
                       collect(DISTINCT f.name) as festivals
            """, name=plant_name)
            record = result.single()
            if record:
                return {
                    "name": record["name"],
                    "latin": record["latin_name"],
                    "family": record["family"],
                    "genus": record["genus"],
                    "distribution": record["distribution"] or "暂无分布信息",
                    "folk_use": record["folk_use"] or "暂无民俗用途",
                    "ecological": record["ecological"] or "暂无生态意义",
                    "cultural_symbol": record["cultural_symbol"] or "暂无文化象征",
                    "symbols": record["symbols"],
                    "medicinal": record["medicinal"],
                    "literature": record["literature"],
                    "festivals": record["festivals"]
                }
            return None

    def close(self):
        self.driver.close()


class LangChainPlantQA:
    """
    基于 LangChain 0.1.0 的智能问答类（不使用 langchain-neo4j 包）。
    """
    def __init__(self, uri=None, user=None, password=None, database=None, groq_api_key=None):
        # 获取数据库名称（优先使用传入参数，其次环境变量，最后默认实例 ID）
        self.database = database or os.environ.get("NEO4J_DATABASE", "60369e3e")
        
        # 连接 Neo4j（使用 langchain.graphs.Neo4jGraph，并指定数据库名）
        self.graph = Neo4jGraph(
            url=uri or os.environ.get("NEO4J_URI"),
            username=user or os.environ.get("NEO4J_USER"),
            password=password or os.environ.get("NEO4J_PASSWORD"),
            database=self.database   # 关键：指定正确的数据库名
        )
        # 初始化 Groq LLM
        self.llm = ChatGroq(
            groq_api_key=groq_api_key or os.environ.get("GROQ_API_KEY"),
            model_name="llama3-8b-8192",
            temperature=0
        )

        # 自定义 Cypher 生成提示词
        CYPHER_GENERATION_TEMPLATE = """你是一个 Neo4j 专家，根据用户问题生成 Cypher 查询。
图数据库包含以下节点和关系：
- 节点标签：Plant（植物）
- 植物属性：name（植物中文名）、latin_name（拉丁名）、family（科）、genus（属）、distribution（分布）、cultural_symbol（文化象征）、folk_use（民俗用途）、medicinal_value（药用价值）
- 关系类型：HAS_SYMBOL（指向 Symbol 节点）、HAS_MEDICINAL（指向 Medicinal 节点）、RECORDED_IN（指向 Literature 节点）、RELATED_TO_FESTIVAL（指向 Festival 节点）
- Symbol 节点属性：meaning（象征意义）
- Medicinal 节点属性：effect（药用功效）
- Literature 节点属性：name（文献名）
- Festival 节点属性：name（节日名）

请只返回 Cypher 查询，不要包含其他解释。
问题：{question}
Cypher 查询："""
        CYPHER_GENERATION_PROMPT = PromptTemplate(
            input_variables=["question"], template=CYPHER_GENERATION_TEMPLATE
        )

        # 创建问答链（langchain 0.1.0 版本参数）
        self.chain = GraphCypherQAChain.from_llm(
            graph=self.graph,
            llm=self.llm,
            cypher_prompt=CYPHER_GENERATION_PROMPT,
            verbose=True,
            return_intermediate_steps=False,
        )

    def answer(self, question: str) -> str:
        try:
            # 0.1.0 版本使用 run 方法
            result = self.chain.run(question)
            return result
        except Exception as e:
            return f"智能问答出错：{str(e)}"


def test():
    qa = PlantQASystem()
    test_qs = [
        "兰有什么文化象征？",
        "菊花的药用价值是什么？",
        "梅花分布在哪里？",
        "端午节和什么植物有关？",
        "玫瑰有什么文化象征？",
        "所有植物有哪些？"
    ]
    print("\n" + "="*60)
    print("🌿 荆楚植物知识图谱问答系统测试")
    print("="*60)
    for q in test_qs:
        print(f"\n❓ {q}")
        print(f"💬 {qa.answer(q)}")
    qa.close()


if __name__ == "__main__":
    test()