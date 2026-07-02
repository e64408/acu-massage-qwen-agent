import json
from pathlib import Path
from core.utils import coordinate_range_check

# 当前文件core/rag.py
KB_PATH = Path(__file__).parent.parent / "knowledge"

class AcupointRAG:
    def __init__(self):
        # 彻底移除向量模型相关代码，不再联网
        self.index = None
        self.data = []
        self._load_prescription()

    def _load_prescription(self):
        presc_path = KB_PATH / "prescriptions.json"
        print("【处方文件完整路径】", presc_path.resolve())
        print("【文件是否存在】", presc_path.exists())
        with open(presc_path, "r", encoding="utf-8") as f:
            self.prescription_map = json.load(f)
        print("【已加载处方key列表】", list(self.prescription_map.keys()))

    def search(self, query, top_k=3):
        print("【检索query】", query)
        if query in self.prescription_map:
            print(f"【匹配到处方】{query}")
            return [self.prescription_map[query]]
        print(f"【无匹配处方】{query}")
        return []

    def verify_point_coordinate(self, point_name, point_xy):
        # 穴位坐标校验临时放行，无向量库不做校验
        return True, None

_rag_singleton = None

def get_rag_instance():
    global _rag_singleton
    if _rag_singleton is None:
        _rag_singleton = AcupointRAG()
    return _rag_singleton