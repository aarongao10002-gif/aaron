"""
DSL 生成器 - 核心模块，协调整个流程
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from llm_processor import LLMProcessor
from dsl_validator import DSLValidator


logger = logging.getLogger(__name__)


class DSLGenerator:
    """AI 智能体架构师 - DSL 生成器"""

    def __init__(self, llm_base_url: str = "http://localhost:11434", model: str = "qwen:8b"):
        """
        初始化 DSL 生成器
        
        Args:
            llm_base_url: LLM 服务地址
            model: 使用的模型
        """
        self.llm_processor = LLMProcessor(base_url=llm_base_url, model=model)
        self.validator = DSLValidator()
        self.history: List[Dict[str, Any]] = []

    def generate_from_requirement(self, requirement: str) -> Dict[str, Any]:
        """
        从自然语言需求生成 DSL
        
        步骤 1: 解析用户指令
        步骤 2: 提取关键信息
        步骤 3: 生成 DSL 结构
        步骤 4: 验证与优化
        
        Args:
            requirement: 用户的自然语言需求
            
        Returns:
            包含 DSL 和验证结果的字典
        """
        logger.info("=" * 50)
        logger.info("开始生成 DSL")
        logger.info("=" * 50)
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # 步骤 1: 解析用户指令
            logger.info("步骤 1: 解析用户指令...")
            result["steps"]["parse_requirement"] = {
                "input": requirement,
                "status": "completed"
            }
            
            # 步骤 2: 提取关键信息
            logger.info("步骤 2: 提取关键信息...")
            extracted_info = self.llm_processor.process_requirement(requirement)
            result["steps"]["extract_info"] = {
                "status": "completed",
                "extracted": extracted_info
            }
            
            # 步骤 3: 生成 DSL 结构
            logger.info("步骤 3: 生成 DSL 结构...")
            dsl = self.llm_processor.generate_dsl_structure(extracted_info)
            
            # 标准化 DSL 格式
            dsl = self._standardize_dsl_format(dsl)
            
            result["steps"]["generate_dsl"] = {
                "status": "completed",
                "dsl_preview": self._dsl_preview(dsl)
            }
            
            # 步骤 4: 验证与优化
            logger.info("步骤 4: 验证与优化...")
            valid, errors, warnings = self.validator.validate(dsl)
            
            result["steps"]["validate_dsl"] = {
                "status": "completed",
                "is_valid": valid,
                "errors": errors,
                "warnings": warnings
            }
            
            # 如果验证不通过，尝试修复
            if not valid and errors:
                logger.warning(f"DSL 验证失败，尝试修复...")
                dsl = self._fix_dsl_errors(dsl, errors)
                valid, errors, warnings = self.validator.validate(dsl)
                result["steps"]["validate_dsl"]["fixed"] = True
                result["steps"]["validate_dsl"]["is_valid"] = valid
                result["steps"]["validate_dsl"]["errors"] = errors
            
            # 完整输出
            result["dsl"] = dsl
            result["is_valid"] = valid
            result["errors"] = errors
            result["warnings"] = warnings
            
            # 记录历史
            self.history.append(result)
            
            logger.info("=" * 50)
            logger.info(f"生成完成！DSL 有效性: {valid}")
            logger.info("=" * 50)
            
            return result
        
        except Exception as e:
            logger.error(f"生成过程出错: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
            return result

    def _standardize_dsl_format(self, dsl: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化 DSL 格式以符合 Dify 要求
        
        Args:
            dsl: 原始 DSL
            
        Returns:
            标准化后的 DSL
        """
        logger.info("标准化 DSL 格式...")
        
        # 确保基本字段存在
        if "version" not in dsl:
            dsl["version"] = "0.1"
        
        if "nodes" not in dsl or not dsl["nodes"]:
            logger.warning("DSL 中没有节点，使用默认结构")
            dsl["nodes"] = []
        
        # 标准化每个节点
        standardized_nodes = []
        for node in dsl.get("nodes", []):
            standardized_node = self._standardize_node(node)
            standardized_nodes.append(standardized_node)
        
        dsl["nodes"] = standardized_nodes
        
        # 确保元数据存在
        if "metadata" not in dsl:
            dsl["metadata"] = {}
        
        # 添加必要的元数据字段
        if "name" not in dsl["metadata"]:
            dsl["metadata"]["name"] = "生成的智能体工作流"
        
        if "description" not in dsl["metadata"]:
            dsl["metadata"]["description"] = "使用 AI Agent Architect 生成"
        
        if "version" not in dsl["metadata"]:
            dsl["metadata"]["version"] = "0.1.0"
        
        return dsl

    def _standardize_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化单个节点
        
        Args:
            node: 节点数据
            
        Returns:
            标准化后的节点
        """
        standardized = {
            "id": node.get("id", "node"),
            "type": node.get("type", "llm"),
        }
        
        # 添加可选字段
        if "name" in node:
            standardized["name"] = node["name"]
        
        if "description" in node:
            standardized["description"] = node["description"]
        
        # 配置字段
        if "config" in node:
            standardized["config"] = node["config"]
        else:
            standardized["config"] = {}
        
        # 确保 LLM 节点有必要的配置
        if standardized["type"] == "llm":
            if "model" not in standardized["config"]:
                standardized["config"]["model"] = "qwen:8b"
            if "prompt" not in standardized["config"]:
                standardized["config"]["prompt"] = "请处理用户输入"
            if "temperature" not in standardized["config"]:
                standardized["config"]["temperature"] = 0.7
            if "max_tokens" not in standardized["config"]:
                standardized["config"]["max_tokens"] = 2048
        
        # 输入和输出
        if "inputs" in node:
            standardized["inputs"] = node["inputs"] if isinstance(node["inputs"], list) else [node["inputs"]]
        else:
            standardized["inputs"] = []
        
        if "outputs" in node:
            standardized["outputs"] = node["outputs"] if isinstance(node["outputs"], list) else [node["outputs"]]
        else:
            standardized["outputs"] = []
        
        return standardized

    def _dsl_preview(self, dsl: Dict[str, Any]) -> str:
        """生成 DSL 的预览字符串"""
        nodes = dsl.get("nodes", [])
        node_ids = [n.get("id", "unknown") for n in nodes]
        return f"节点数: {len(nodes)}, 节点: {', '.join(node_ids)}"

    def _fix_dsl_errors(self, dsl: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """
        尝试修复 DSL 中的错误
        
        Args:
            dsl: 原始 DSL
            errors: 错误列表
            
        Returns:
            修复后的 DSL
        """
        logger.info(f"尝试修复 DSL 错误: {errors}")
        
        # 修复缺少的 input 节点
        if "工作流必须至少有一个 'input' 节点" in errors[0] if errors else False:
            dsl["nodes"].insert(0, {
                "id": "input",
                "type": "input",
                "name": "输入节点",
                "outputs": [dsl["nodes"][0]["id"] if dsl["nodes"] else "output"]
            })
        
        # 修复缺少的 output 节点
        if "工作流必须至少有一个 'output' 节点" in errors[0] if errors else False:
            dsl["nodes"].append({
                "id": "output",
                "type": "output",
                "name": "输出节点",
                "inputs": [dsl["nodes"][-1]["id"] if dsl["nodes"] else "input"]
            })
        
        return dsl

    def validate_dsl(self, dsl: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证 DSL
        
        Args:
            dsl: DSL 字典
            
        Returns:
            验证结果
        """
        valid, errors, warnings = self.validator.validate(dsl)
        return {
            "is_valid": valid,
            "errors": errors,
            "warnings": warnings
        }

    def save_dsl(self, dsl: Dict[str, Any], filepath: str) -> bool:
        """
        保存 DSL 到文件
        
        Args:
            dsl: DSL 字典
            filepath: 保存路径
            
        Returns:
            是否保存成功
        """
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # 标准化格式后保存
            standardized_dsl = self._standardize_dsl_format(dsl.copy())
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(standardized_dsl, f, indent=2, ensure_ascii=False)
            
            logger.info(f"DSL 已保存到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存 DSL 失败: {str(e)}")
            return False

    def load_dsl(self, filepath: str) -> Dict[str, Any]:
        """
        加载 DSL 文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            DSL 字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dsl = json.load(f)
            logger.info(f"DSL 已加载: {filepath}")
            return dsl
        except Exception as e:
            logger.error(f"加载 DSL 失败: {str(e)}")
            return {}

    def export_dsl_for_dify(self, dsl: Dict[str, Any]) -> str:
        """
        导出 DSL 为 Dify 可导入的格式
        
        Args:
            dsl: DSL 字典
            
        Returns:
            JSON 字符串
        """
        # 确保 DSL 包含必要的 Dify 字段
        dsl_copy = dsl.copy()
        
        # 标准化格式
        dsl_copy = self._standardize_dsl_format(dsl_copy)
        
        return json.dumps(dsl_copy, indent=2, ensure_ascii=False)

    def optimize_dsl(self, dsl: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化 DSL（后期可添加更多优化逻辑）
        
        Args:
            dsl: 原始 DSL
            
        Returns:
            优化后的 DSL
        """
        dsl_copy = dsl.copy()
        
        # 标准化格式
        dsl_copy = self._standardize_dsl_format(dsl_copy)
        
        # 添加优化元数据
        if "metadata" not in dsl_copy:
            dsl_copy["metadata"] = {}
        
        dsl_copy["metadata"]["optimized"] = True
        dsl_copy["metadata"]["optimized_at"] = datetime.now().isoformat()
        
        logger.info("DSL 优化完成")
        return dsl_copy

    def get_history(self) -> List[Dict[str, Any]]:
        """获取生成历史"""
        return self.history

    def clear_history(self) -> None:
        """清空生成历史"""
        self.history = []
        logger.info("生成历史已清空")
