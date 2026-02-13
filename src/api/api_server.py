#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荆楚植物图谱 API接口服务
用于小程序/APP/其他前端调用，免费基于FastAPI
运行命令：python api_server.py
接口文档：http://localhost:8000/docs
"""
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_qa import LangChainPlantQA
import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
# 初始化FastAPI
app = FastAPI(
    title="荆楚植物文化图谱API",
    description="提供植物问答、植物详情、植物列表等接口，适配小程序/APP",
    version="1.0.0"
)
# 初始化问答实例（缓存）
qa = LangChainPlantQA()

# 定义请求模型
class QuestionRequest(BaseModel):
    question: str  # 自然语言问题

class PlantDetailRequest(BaseModel):
    plant_name: str  # 植物中文名

# ==================== 接口定义 ====================
@app.get("/api/plant_list", summary="获取所有植物名称列表")
def get_plant_list():
    """返回Neo4j中所有荆楚植物的中文名列表"""
    try:
        return {"code": 200, "data": qa.plant_names, "msg": "success"}
    except Exception as e:
        return {"code": 500, "data": [], "msg": f"获取失败: {str(e)}"}

@app.post("/api/plant_detail", summary="获取单株植物的完整详情")
def get_plant_detail(req: PlantDetailRequest):
    """根据植物中文名，返回科属、分布、象征、药用等完整信息"""
    try:
        detail = qa.get_plant_detail(req.plant_name)
        return {"code": 200, "data": detail, "msg": "success"}
    except Exception as e:
        return {"code": 500, "data": None, "msg": f"获取失败: {str(e)}"}

@app.post("/api/answer", summary="智能问答接口（自然语言）")
def answer_question(req: QuestionRequest):
    """输入任意自然语言问题，返回Cypher查询结果"""
    try:
        answer = qa.answer(req.question)
        return {"code": 200, "data": answer, "msg": "success"}
    except Exception as e:
        return {"code": 500, "data": "", "msg": f"问答失败: {str(e)}"}

# 主函数
if __name__ == "__main__":
    # 启动API服务，本地访问：http://localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
    print("✅ API服务已启动，接口文档：http://localhost:8000/docs")