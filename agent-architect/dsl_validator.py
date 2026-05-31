"""
DSL 验证器 - 验证生成的 DSL 文件合法性
"""

import json
from typing import Dict, List, Tuple, Any
from jsonschema import validate, ValidationError


class DSLValidator:
    """验证 Dify DSL 的合法性和完整性"""

    # DSL Schema 定义
    DSL_SCHEMA = {
        "type": "object",
        "required": ["version", "nodes"],
        "properties": {
            "version": {
                "type": "string",
                "pattern": r"^\d+\.\d+$"
            },
            "nodes": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "object",
                    "required": ["id", "type"],
                    "properties": {
                        "id": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z0-9_-]+$"
                        },
                        "type": {
                            "type": "string",
                            "enum": ["input", "llm", "function", "output", "condition", "loop"]
                        },
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "config": {"type": "object"},
                        "inputs": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "outputs": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "author": {"type": "string"},
                    "version": {"type": "string"},
                    "created_at": {"type": "string"},
                    "input_fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "output_fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }

    def __init__(self):
        """初始化验证器"""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, dsl: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证 DSL 的合法性
        
        Args:
            dsl: DSL 字典对象
            
        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        self.errors = []
        self.warnings = []
        
        # 1. Schema 验证
        self._validate_schema(dsl)
        if self.errors:
            return False, self.errors, self.warnings
        
        # 2. 节点连接验证
        self._validate_node_connections(dsl.get("nodes", []))
        
        # 3. 业务逻辑验证
        self._validate_business_logic(dsl)
        
        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_schema(self, dsl: Dict[str, Any]) -> None:
        """验证 DSL 是否符合 Schema"""
        try:
            validate(instance=dsl, schema=self.DSL_SCHEMA)
        except ValidationError as e:
            self.errors.append(f"Schema 验证失败: {e.message}")

    def _validate_node_connections(self, nodes: List[Dict[str, Any]]) -> None:
        """验证节点之间的连接关系"""
        node_ids = {node["id"] for node in nodes}
        node_map = {node["id"]: node for node in nodes}
        
        # 检查输入/输出是否存在
        for node in nodes:
            for input_id in node.get("inputs", []):
                if input_id not in node_ids:
                    self.errors.append(f"节点 '{node['id']}' 的输入 '{input_id}' 不存在")
            
            for output_id in node.get("outputs", []):
                if output_id not in node_ids:
                    self.errors.append(f"节点 '{node['id']}' 的输出 '{output_id}' 不存在")
        
        # 检查入度和出度
        in_degree = {node_id: 0 for node_id in node_ids}
        out_degree = {node_id: 0 for node_id in node_ids}
        
        for node in nodes:
            for output_id in node.get("outputs", []):
                out_degree[node["id"]] += 1
                in_degree[output_id] += 1
        
        # Input 节点不能有输入
        input_nodes = [n for n in nodes if n["type"] == "input"]
        for node in input_nodes:
            if node.get("inputs"):
                self.errors.append(f"Input 节点 '{node['id']}' 不应该有输入")
        
        # Output 节点不能有输出
        output_nodes = [n for n in nodes if n["type"] == "output"]
        for node in output_nodes:
            if node.get("outputs"):
                self.errors.append(f"Output 节点 '{node['id']}' 不应该有输出")

    def _validate_business_logic(self, dsl: Dict[str, Any]) -> None:
        """验证业务逻辑的合理性"""
        nodes = dsl.get("nodes", [])
        
        # 检查必须有 input 和 output 节点
        has_input = any(n["type"] == "input" for n in nodes)
        has_output = any(n["type"] == "output" for n in nodes)
        
        if not has_input:
            self.errors.append("工作流必须至少有一个 'input' 节点")
        if not has_output:
            self.errors.append("工作流必须至少有一个 'output' 节点")
        
        # 检查 LLM 节点的配置
        for node in nodes:
            if node["type"] == "llm":
                config = node.get("config", {})
                if not config.get("model"):
                    self.warnings.append(f"LLM 节点 '{node['id']}' 未指定模型")
                if not config.get("prompt"):
                    self.warnings.append(f"LLM 节点 '{node['id']}' 未指定 prompt")

    def validate_json_string(self, dsl_json: str) -> Tuple[bool, List[str], List[str]]:
        """验证 JSON 字符串格式的 DSL"""
        try:
            dsl = json.loads(dsl_json)
            return self.validate(dsl)
        except json.JSONDecodeError as e:
            return False, [f"JSON 格式错误: {str(e)}"], []


if __name__ == "__main__":
    # 测试
    validator = DSLValidator()
    
    sample_dsl = {
        "version": "0.1",
        "nodes": [
            {
                "id": "input",
                "type": "input",
                "name": "用户输入",
                "outputs": ["llm_1"]
            },
            {
                "id": "llm_1",
                "type": "llm",
                "name": "文本分类",
                "config": {
                    "model": "qwen:8b",
                    "prompt": "请对以下文本进行分类..."
                },
                "inputs": ["input"],
                "outputs": ["output"]
            },
            {
                "id": "output",
                "type": "output",
                "name": "输出结果",
                "inputs": ["llm_1"]
            }
        ],
        "metadata": {
            "name": "简单文本分类",
            "description": "基础文本分类工作流"
        }
    }
    
    valid, errors, warnings = validator.validate(sample_dsl)
    print(f"验证结果: {valid}")
    if errors:
        print(f"错误: {errors}")
    if warnings:
        print(f"警告: {warnings}")
