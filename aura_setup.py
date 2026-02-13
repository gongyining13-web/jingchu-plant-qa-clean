"""
Neo4j Aura API 自动化配置脚本
功能：添加 IP 白名单、重置密码、输出连接信息
"""

import requests
import json
import base64
import time
from getpass import getpass

# ====== 请填写您的信息 ======
INSTANCE_ID = "d61cfc91"          # 您的新实例ID
CLIENT_ID = "6hNGVaJ0NgMB7nQlDdHbBJd3Os3iWXds"       # 从控制台复制的
CLIENT_SECRET = "f68WUiogn-OWJ5PiTSNM05r5ufr3paAWcrs1BVRKbnxajB9-MmKTMfaEJimaiua6"  # 从控制台复制的
# =============================

def get_access_token(client_id, client_secret):
    """获取 API 访问令牌"""
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(
        "https://api.neo4j.io/oauth/token",
        headers=headers,
        data=data
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ 获取令牌失败: {response.text}")
        return None

def add_ip_whitelist(instance_id, token):
    """添加 IP 白名单 0.0.0.0/0"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "access": [{
            "cidr": "0.0.0.0/0",
            "description": "Allow all IPs"
        }]
    }
    
    response = requests.post(
        f"https://api.neo4j.io/v1/instances/{instance_id}/ip-access",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        print("✅ IP白名单添加成功！")
        return True
    else:
        print(f"❌ 添加失败: {response.text}")
        return False

def reset_password(instance_id, token):
    """重置实例密码，返回新密码"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"https://api.neo4j.io/v1/instances/{instance_id}/password",
        headers=headers
    )
    
    if response.status_code == 201:
        new_password = response.json()["temporary_password"]
        print("✅ 密码重置成功！")
        print(f"🔑 新密码: {new_password}")
        print("⚠️ 请立即保存此密码！")
        return new_password
    else:
        print(f"❌ 重置密码失败: {response.text}")
        return None

def get_instance_uri(instance_id, token):
    """获取实例连接URI"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"https://api.neo4j.io/v1/instances/{instance_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        uri = data["connection_url"].replace("neo4j://", "neo4j+s://")
        return uri
    else:
        print(f"❌ 获取URI失败: {response.text}")
        return None

def main():
    print("🔧 Neo4j Aura 自动化配置工具")
    print("="*50)
    
    # 1. 获取令牌
    print("1️⃣ 正在获取访问令牌...")
    token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    if not token:
        return
    print("✅ 令牌获取成功")
    
    # 2. 添加IP白名单
    print("2️⃣ 正在添加IP白名单...")
    if not add_ip_whitelist(INSTANCE_ID, token):
        return
    
    # 3. 获取实例URI
    print("3️⃣ 正在获取连接地址...")
    uri = get_instance_uri(INSTANCE_ID, token)
    if not uri:
        return
    print(f"✅ 连接地址: {uri}")
    
    # 4. 重置密码（获取新密码）
    print("4️⃣ 正在重置密码...")
    new_pass = reset_password(INSTANCE_ID, token)
    if not new_pass:
        return
    
    # 5. 输出最终配置
    print("\n" + "="*50)
    print("🎉 配置完成！以下是您的云数据库连接信息：")
    print("="*50)
    print(f"NEO4J_URI = \"{uri}\"")
    print("NEO4J_USER = \"neo4j\"")
    print(f"NEO4J_PASSWORD = \"{new_pass}\"")
    print("="*50)
    print("⚠️ 请立即将以上信息复制到 Streamlit Secrets！")
    print("⚠️ 此密码只显示一次，忘记后需再次重置。")

if __name__ == "__main__":
    main()