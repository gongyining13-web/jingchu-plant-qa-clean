#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Excel 数据导入 Neo4j 数据库
"""
import pandas as pd
from neo4j import GraphDatabase
import os

# Neo4j 连接配置
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "12345678")

def import_data(excel_path):
    # 读取 Excel 数据
    df = pd.read_excel(excel_path)
    
    # 连接 Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 清空现有数据（可选）
        session.run("MATCH (n) DETACH DELETE n")
        
        # 导入植物节点
        for _, row in df.iterrows():
            session.run("""
                CREATE (p:Plant {
                    id: $id,
                    name: $name,
                    latin_name: $latin_name,
                    family: $family,
                    genus: $genus,
                    distribution: $distribution,
                    folk_use: $folk_use,
                    ecological_meaning: $ecological_meaning,
                    cultural_symbol: $cultural_symbol,
                    medicinal_value: $medicinal_value,
                    literature_source: $literature_source,
                    festival: $festival
                })
            """, 
            id=row["id"],
            name=row["name"],
            latin_name=row["latin_name"],
            family=row["family"],
            genus=row["genus"],
            distribution=row["distribution"],
            folk_use=row["folk_use"],
            ecological_meaning=row["ecological_meaning"],
            cultural_symbol=row["cultural_symbol"],
            medicinal_value=row["medicinal_value"],
            literature_source=row["literature_source"],
            festival=row["festival"]
            )
        
        # 导入药用价值关系（示例）
        session.run("""
            MATCH (p:Plant), (m:Medicinal)
            WHERE p.medicinal_value IS NOT NULL
            CREATE (p)-[:HAS_MEDICINAL]->(m:Medicinal {effect: p.medicinal_value})
        """)
        
        print("数据导入完成！")
    
    driver.close()

if __name__ == "__main__":
    # 替换为你的 Excel 文件路径
    import_data("../../data/荆楚植物文化图谱植物数据.xlsx")