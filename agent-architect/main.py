"""
AI 智能体架构师 - 主服务入口
FastAPI 服务，提供 HTTP API 接口
"""

import json
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
import uvicorn
import yaml

from dsl_generator import DSLGenerator


# ============== 配置 ==============
# 加载配置文件
CONFIG_FILE = "config.yaml"

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "llm": {
                "base_url": "http://localhost:11434",
                "model": "qwen:8b"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000
            }
        }

config = load_config()

# ============== 日志配置 ==============
logging.basicConfig(
    level=config.get("logging", {}).get("level", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============== Pydantic 模型 ==============

class GenerateRequest(BaseModel):
    """生成 DSL 的请求模型"""
    requirement: str = Field(
        ..., 
        description="用户的自然语言需求描述",
        example="我需要一个智能体，能根据用户输入的查询，调用搜索工具并返回结果。"
    )
    save_to_file: Optional[bool] = Field(
        False,
        description="是否保存生成的 DSL 到文件"
    )


class ValidateRequest(BaseModel):
    """验证 DSL 的请求模型"""
    dsl: dict = Field(..., description="Dify DSL 配置")


class OptimizeRequest(BaseModel):
    """优化 DSL 的请求模型"""
    dsl: dict = Field(..., description="Dify DSL 配置")


class DSLResponse(BaseModel):
    """DSL 生成响应模型"""
    status: str = Field(..., description="状态: success 或 error")
    timestamp: str = Field(..., description="时间戳")
    dsl: Optional[dict] = Field(None, description="生成的 DSL")
    is_valid: bool = Field(False, description="DSL 是否有效")
    errors: list = Field(default_factory=list, description="错误列表")
    warnings: list = Field(default_factory=list, description="警告列表")
    message: Optional[str] = Field(None, description="消息")


# ============== FastAPI 应用 ==============

app = FastAPI(
    title="AI 智能体架构师",
    description="根据自然语言需求自动生成 Dify DSL 工作流配置",
    version="0.1.0"
)

# 全局 DSL 生成器实例
generator = DSLGenerator(
    llm_base_url=config.get("llm", {}).get("base_url", "http://localhost:11434"),
    model=config.get("llm", {}).get("model", "qwen:8b")
)


# ============== API 路由 ==============

@app.get("/")
async def root():
    """获取服务信息"""
    return {
        "name": "AI 智能体架构师",
        "version": "0.1.0",
        "description": "根据自然语言需求自动生成 Dify DSL 工作流配置",
        "endpoints": {
            "generate": "/api/generate",
            "validate": "/api/validate",
            "optimize": "/api/optimize",
            "history": "/api/history",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    try:
        # 尝试连接 LLM
        generator.llm_processor._call_llm("test")
        return {
            "status": "healthy",
            "llm": f"{config['llm']['model']} at {config['llm']['base_url']}",
            "message": "服务运行正常"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "无法连接到 LLM 服务"
        }


@app.post("/api/generate", response_model=DSLResponse)
async def generate_dsl(request: GenerateRequest):
    """
    生成 DSL
    
    ## 步骤：
    1. 解析用户指令
    2. 提取关键信息
    3. 生成 DSL 结构
    4. 验证与优化
    
    ## 示例请求：
    ```json
    {
        "requirement": "我需要一个智能体，能根据用户输入的查询，调用搜索工具并返回结果。输入字段是'query'，输出字段是'result'。"
    }
    ```
    """
    logger.info(f"生成请求: {request.requirement[:100]}...")
    
    try:
        # 生成 DSL
        result = generator.generate_from_requirement(request.requirement)
        
        # 保存文件
        if request.save_to_file and result["status"] == "success":
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            filepath = output_dir / "generated_dsl.json"
            generator.save_dsl(result["dsl"], str(filepath))
            result["saved_to"] = str(filepath)
        
        return DSLResponse(
            status=result.get("status", "error"),
            timestamp=result.get("timestamp", ""),
            dsl=result.get("dsl"),
            is_valid=result.get("is_valid", False),
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            message=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate")
async def validate_dsl(request: ValidateRequest):
    """
    验证 DSL 的合法性
    
    ## 验证内容：
    - Schema 验证
    - 节点连接验证
    - 业务逻辑验证
    """
    logger.info("验证 DSL...")
    
    try:
        result = generator.validate_dsl(request.dsl)
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize")
async def optimize_dsl(request: OptimizeRequest):
    """
    优化 DSL 配置
    """
    logger.info("优化 DSL...")
    
    try:
        optimized_dsl = generator.optimize_dsl(request.dsl)
        
        # 验证优化后的 DSL
        validation_result = generator.validate_dsl(optimized_dsl)
        
        return {
            "status": "success",
            "optimized_dsl": optimized_dsl,
            "validation": validation_result
        }
    except Exception as e:
        logger.error(f"优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history():
    """获取生成历史"""
    history = generator.get_history()
    return {
        "status": "success",
        "total": len(history),
        "history": history[-10:]  # 返回最后 10 条
    }


@app.delete("/api/history")
async def clear_history():
    """清空生成历史"""
    generator.clear_history()
    return {"status": "success", "message": "历史已清空"}


@app.post("/api/export")
async def export_dsl(request: Body(..., media_type="application/json")):
    """
    导出 DSL 为 Dify 可导入的格式
    """
    try:
        dsl_json = generator.export_dsl_for_dify(request)
        return {
            "status": "success",
            "dsl_json": dsl_json
        }
    except Exception as e:
        logger.error(f"导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== 启动函数 ==============

def main():
    """启动服务"""
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    reload = server_config.get("reload", False)
    
    logger.info(f"启动 AI 智能体架构师服务")
    logger.info(f"地址: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/docs")
    logger.info(f"模型: {config['llm']['model']}")
    logger.info(f"LLM 服务: {config['llm']['base_url']}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=server_config.get("log_level", "info")
    )


if __name__ == "__main__":
    main()
