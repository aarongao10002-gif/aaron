"""
LLM 处理模块 - 使用本地 Qwen3:8b 模型处理自然语言需求
"""

import json
import requests
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProcessor:
    """使用 Ollama 本地模型处理自然语言请求"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen:8b"):
        """
        初始化 LLM 处理器
        
        Args:
            base_url: Ollama 服务地址
            model: 模型名称
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

    def process_requirement(self, requirement: str) -> Dict[str, Any]:
        """
        处理用户需求，提取关键信息
        
        Args:
            requirement: 用户的自然语言需求
            
        Returns:
            包含提取信息的字典
        """
        logger.info(f"处理需求: {requirement[:100]}...")
        
        # 构建提示词
        prompt = self._build_extraction_prompt(requirement)
        
        # 调用 LLM
        response = self._call_llm(prompt)
        
        # 解析响应
        extracted_info = self._parse_extraction_response(response)
        
        logger.info(f"提取结果: {extracted_info}")
        return extracted_info

    def _build_extraction_prompt(self, requirement: str) -> str:
        """构建信息提取的提示词"""
        prompt = f"""请分析以下智能体需求，并以 JSON 格式提取关键信息：

需求描述：
{requirement}

请返回以下信息的 JSON 对象（不要包含任何额外文本）：
{{
    "agent_name": "智能体名称",
    "agent_description": "智能体描述",
    "input_fields": [
        {{"name": "字段名", "type": "string/number/object", "description": "字段描述"}}
    ],
    "output_fields": [
        {{"name": "字段名", "type": "string/number/object", "description": "字段描述"}}
    ],
    "components_needed": ["llm", "function", "condition"] // 需要的组件
}}"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        调用本地 LLM 模型
        
        Args:
            prompt: 提示词
            
        Returns:
            模型返回的文本
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            logger.debug(f"调用 LLM: {self.model}")
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except requests.exceptions.ConnectionError:
            logger.error(f"无法连接到 Ollama 服务: {self.base_url}")
            raise Exception(f"Ollama 服务不可用，请确保在 {self.base_url} 运行")
        
        except Exception as e:
            logger.error(f"LLM 调用失败: {str(e)}")
            raise

    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 的响应
        
        Args:
            response: LLM 返回的文本
            
        Returns:
            解析后的字典
        """
        try:
            # 尝试找到 JSON 对象
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)
                return parsed
            else:
                logger.warning("无法在响应中找到 JSON 对象")
                return self._default_extraction_result()
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {str(e)}")
            return self._default_extraction_result()

    @staticmethod
    def _default_extraction_result() -> Dict[str, Any]:
        """返回默认的提取结果"""
        return {
            "agent_name": "新建智能体",
            "agent_description": "暂无描述",
            "input_fields": [
                {"name": "query", "type": "string", "description": "用户查询"}
            ],
            "output_fields": [
                {"name": "result", "type": "string", "description": "处理结果"}
            ],
            "components_needed": ["llm", "function"]
        }

    def generate_dsl_structure(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据提取的信息生成 DSL 结构框架
        
        Args:
            extracted_info: 提取的关键信息
            
        Returns:
            DSL 结构
        """
        logger.info("生成 DSL 结构...")
        
        # 提示词
        prompt = self._build_dsl_generation_prompt(extracted_info)
        
        # 调用 LLM 生成 DSL
        response = self._call_llm(prompt)
        
        # 解析返回的 DSL
        dsl = self._parse_dsl_response(response, extracted_info)
        
        logger.info("DSL 结构生成完成")
        return dsl

    def _build_dsl_generation_prompt(self, extracted_info: Dict[str, Any]) -> str:
        """构建 DSL 生成的提示词"""
        
        input_fields = extracted_info.get("input_fields", [])
        output_fields = extracted_info.get("output_fields", [])
        components = extracted_info.get("components_needed", ["llm"])
        
        input_str = ", ".join([f['name'] for f in input_fields])
        output_str = ", ".join([f['name'] for f in output_fields])
        
        prompt = f"""根据以下要求生成 Dify DSL 工作流配置（JSON 格式）：

智能体信息：
- 名称：{extracted_info.get('agent_name', '新智能体')}
- 描述：{extracted_info.get('agent_description', '暂无')}
- 输入字段：{input_str}
- 输出字段：{output_str}
- 需要的组件：{", ".join(components)}

请生成一个有效的 Dify DSL JSON（只返回 JSON，不要其他文本）：
{{
    "version": "0.1",
    "nodes": [
        // 包含 input、各个处理节点、output
    ],
    "metadata": {{
        "name": "...",
        "description": "...",
        "input_fields": [...],
        "output_fields": [...]
    }}
}}

节点类型参考：
- input：输入节点，接收用户输入
- llm：大语言模型节点，用于文本处理/分类
- function：函数调用节点，用于执行特定操作
- output：输出节点，返回最终结果"""
        
        return prompt

    def _parse_dsl_response(self, response: str, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 LLM 生成的 DSL
        
        Args:
            response: LLM 返回的文本
            extracted_info: 提取的信息
            
        Returns:
            完整的 DSL 结构
        """
        try:
            # 尝试找到 JSON 对象
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                dsl = json.loads(json_str)
                
                # 补充元数据
                if "metadata" not in dsl:
                    dsl["metadata"] = {}
                
                dsl["metadata"]["created_at"] = datetime.now().isoformat()
                dsl["metadata"]["input_fields"] = extracted_info.get("input_fields", [])
                dsl["metadata"]["output_fields"] = extracted_info.get("output_fields", [])
                
                return dsl
            else:
                logger.warning("无法从 LLM 响应中提取 DSL")
                return self._default_dsl_structure(extracted_info)
        
        except json.JSONDecodeError as e:
            logger.warning(f"DSL JSON 解析失败: {str(e)}")
            return self._default_dsl_structure(extracted_info)

    @staticmethod
    def _default_dsl_structure(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """返回默认的 DSL 结构"""
        input_field = extracted_info.get("input_fields", [{"name": "query", "type": "string"}])[0]
        output_field = extracted_info.get("output_fields", [{"name": "result", "type": "string"}])[0]
        
        return {
            "version": "0.1",
            "nodes": [
                {
                    "id": "input",
                    "type": "input",
                    "name": "输入节点",
                    "description": f"接收 {input_field['name']} 输入",
                    "outputs": ["llm_process"]
                },
                {
                    "id": "llm_process",
                    "type": "llm",
                    "name": "LLM 处理",
                    "config": {
                        "model": "qwen:8b",
                        "prompt": f"请处理用户输入的 {input_field['name']}，并返回 {output_field['name']}",
                        "temperature": 0.7
                    },
                    "inputs": ["input"],
                    "outputs": ["output"]
                },
                {
                    "id": "output",
                    "type": "output",
                    "name": "输出节点",
                    "description": f"输出 {output_field['name']}",
                    "inputs": ["llm_process"]
                }
            ],
            "metadata": {
                "name": extracted_info.get("agent_name", "新智能体"),
                "description": extracted_info.get("agent_description", ""),
                "created_at": datetime.now().isoformat(),
                "input_fields": extracted_info.get("input_fields", []),
                "output_fields": extracted_info.get("output_fields", [])
            }
        }
