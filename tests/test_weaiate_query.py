import weaviate
from weaviate.auth import AuthApiKey

# === 配置部分 ===
WEAVIATE_URL = "http://localhost:8080"
API_KEY = "root-user-key"  # 替换成你的 key

# === 初始化客户端 ===
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(API_KEY)
)

# === 获取当前集合列表 ===
collections = client.collections.list_all()
print("集合列表：")
for collection in collections:
    print("-", collection.name)

# === 查询某个集合的数据（比如 Document） ===
if "Document" in [c.name for c in collections]:
    document = client.collections.get("Document")

    # 查询前5条数据
    results = document.query.fetch_objects(limit=5)
    print("\nDocument 集合前 5 条数据：")
    for obj in results.objects:
        print(obj.properties)

else:
    print("\n未找到 Document 集合，请检查 Weaviate 中的集合名。")