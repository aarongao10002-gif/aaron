# AI 智能体架构师 (AI Agent Architect)

一个强大的工具，根据自然语言需求自动生成 Dify DSL 工作流配置，支持文本分类、数据查询等场景。

## 功能特性

✨ **核心功能**
- 🤖 **自然语言理解**: 解析用户的自然语言需求
- 🏗️ **自动架构设计**: 基于需求自动提取关键信息并设计工作流
- 📝 **DSL 生成**: 生成标准的 Dify DSL 配置文件
- ✅ **智能验证**: 验证生成的 DSL 合法性和完整性
- 🔧 **优化建议**: 提供工作流优化建议
- 📦 **Dify 集成**: 生成的 DSL 可直接导入 Dify 平台

## 工作流程

```
用户需求 (自然语言)
    ↓
[步骤 1] 解析用户指令
    ↓
[步骤 2] 提取关键信息
    - 输入字段
    - 输出字段
    - 需要的组件
    ↓
[步骤 3] 生成 DSL 结构
    - 创建节点
    - 配置节点参数
    - 连接工作流
    ↓
[步骤 4] 验证与优化
    - Schema 验证
    - 节点连接验证
    - 业务逻辑检查
    ↓
Dify DSL 配置文件 (JSON)
    ↓
导入 Dify 平台 → 自动构建智能体工作流
```

## 技术栈

- **后端**: Python FastAPI
- **LLM**: Ollama + Qwen 3:8b (本地部署)
- **验证**: JSON Schema 验证
- **API**: RESTful API

## 项目结构

```
agent-architect/
├── main.py                 # FastAPI 主服务
├── dsl_generator.py        # DSL 生成器核心模块
├── llm_processor.py        # LLM 处理（Ollama 集成）
├── dsl_validator.py        # DSL 验证器
├── config.yaml             # 配置文件
└── requirements.txt        # 依赖列表

dify-integration/
├── tool_config.json        # Dify 工具配置
└── README.md               # Dify 集成指南
```

## 快速开始

### 前置要求

1. **安装 Python** (>=3.8)
2. **安装 Ollama**
   - 下载: https://ollama.ai
   - 启动服务: `ollama serve`
3. **拉取 Qwen 模型**
   ```bash
   ollama pull qwen:8b
   ```

### 安装与运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/aarongao10002-gif/aaron.git
   cd aaron/agent-architect
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动服务**
   ```bash
   python main.py
   ```

   服务将在 `http://localhost:8000` 启动

4. **查看 API 文档**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API 使用示例

### 生成 DSL

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "我需要一个智能体，能根据用户输入的查询，调用搜索工具并返回结果。输入字段是query，输出字段是result。"
  }'
```

**响应示例：**
```json
{
  "status": "success",
  "timestamp": "2026-05-31T10:30:45.123456",
  "dsl": {
    "version": "0.1",
    "nodes": [
      {
        "id": "input",
        "type": "input",
        "outputs": ["llm_process"]
      },
      {
        "id": "llm_process",
        "type": "llm",
        "config": {"model": "qwen:8b"},
        "inputs": ["input"],
        "outputs": ["output"]
      },
      {
        "id": "output",
        "type": "output",
        "inputs": ["llm_process"]
      }
    ]
  },
  "is_valid": true,
  "errors": [],
  "warnings": []
}
```

### 验证 DSL

```bash
curl -X POST "http://localhost:8000/api/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "dsl": {...}
  }'
```

### 优化 DSL

```bash
curl -X POST "http://localhost:8000/api/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "dsl": {...}
  }'
```

### 获取生成历史

```bash
curl -X GET "http://localhost:8000/api/history"
```

### 健康检查

```bash
curl -X GET "http://localhost:8000/api/health"
```

## Dify 集成指南

### 步骤 1: 启动 AI Agent Architect 服务

```bash
python main.py
```

### 步骤 2: 在 Dify 中添加工具

1. 打开 Dify 工作室
2. 选择 "工具" → "新建工具"
3. 选择 "API" 类型
4. 配置以下信息：
   - **工具名称**: AI Agent Architect
   - **API URL**: http://localhost:8000/api/generate
   - **认证方式**: 无
   - **输入参数**:
     ```json
     {
       "requirement": {
         "type": "string",
         "description": "智能体需求描述"
       }
     }
    ```

### 步骤 3: 在工作流中使用

1. 创建新的工作流
2. 添加 "AI Agent Architect" 工具节点
3. 输入自然语言需求
4. 工具将返回 DSL JSON
5. 将返回的 DSL 导入 Dify 创建新的智能体

### 步骤 4: 导入生成的 DSL

生成的 DSL 可以通过以下方式导入 Dify：

1. Dify 控制面板 → "导入" → 选择 DSL 文件
2. 或复制 JSON 内容直接使用

## 配置说明

编辑 `config.yaml` 自定义配置：

```yaml
# LLM 配置
llm:
  provider: ollama
  model: qwen:8b              # 可改为其他模型
  base_url: http://localhost:11434
  temperature: 0.7
  top_p: 0.9
  max_tokens: 2048

# 服务配置
server:
  host: 0.0.0.0
  port: 8000
  reload: true

# Dify 集成配置
dify:
  tool_name: "AI Agent Architect"
  version: "0.1.0"
```

## 使用案例

### 案例 1: 文本分类智能体

**需求描述：**
```
我需要一个智能体，能对用户输入的文本进行情感分类（正面、中立、负面）。
输入字段是'text'，输出字段是'sentiment'。
```

**生成的工作流：**
- Input: 接收文本输入
- LLM: 使用 Qwen 模型进行情感分析
- Output: 返回分类结果

### 案例 2: 数据查询智能体

**需求描述：**
```
我需要一个智能体，能接收用户的数据查询请求，
调用数据库查询工具，并对结果进行处理和过滤。
输入字段是'query'，输出字段是'result'。
```

**生成的工作流：**
- Input: 接收查询请求
- LLM: 理解查询意图
- Function: 调用数据库工具
- Output: 返回处理后的结果

### 案例 3: 多步骤处理智能体

**需求描述：**
```
我需要一个多步骤智能体：
1) 接收用户输入
2) LLM 理解意图
3) 调用搜索工具
4) 对结果进行分类
5) 返回最终结果
```

## 支持的节点类型

| 节点类型 | 说明 | 用途 |
|---------|------|------|
| `input` | 输入节点 | 接收用户输入 |
| `llm` | 大语言模型节点 | 文本处理、理解、分类 |
| `function` | 函数/工具调用节点 | 执行特定操作、API 调用 |
| `output` | 输出节点 | 返回最终结果 |
| `condition` | 条件分支节点 | 根据条件分流 |
| `loop` | 循环节点 | 重复执行操作 |

## 故障排除

### 问题 1: 无法连接到 Ollama 服务

**症状**: `Error: Ollama 服务不可用`

**解决方案**:
1. 确保 Ollama 已安装并运行
2. 检查 Ollama 服务地址配置（默认 `http://localhost:11434`）
3. 运行 `ollama pull qwen:8b` 确保模型已下载

### 问题 2: DSL 验证失败

**症状**: 生成的 DSL 包含错误

**解决方案**:
1. 检查需求描述是否清晰明确
2. 查看返回的 `errors` 和 `warnings` 字段
3. 使用 `/api/validate` 端点详细验证

### 问题 3: Qwen 模型响应缓慢

**症状**: API 响应时间过长

**解决方案**:
1. 增加模型超时时间（config.yaml 中的 `timeout`）
2. 简化需求描述
3. 考虑使用更小的模型版本

## 后续计划

- [ ] 支持更多 LLM 模型（GPT-4、Claude 等）
- [ ] 可视化工作流编辑器
- [ ] 工作流模板库
- [ ] 高级优化建议
- [ ] 性能监控和分析
- [ ] 多语言支持

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或 Pull Request。
