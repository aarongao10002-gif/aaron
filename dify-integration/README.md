# Dify 集成指南

## 概述

AI 智能体架构师可以与 Dify 平台无缝集成，作为自定义工具，帮助您快速生成 DSL 工作流配置。

## 前置准备

### 1. 启动 AI Agent Architect 服务

```bash
cd agent-architect
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 2. 确保 Ollama 运行

```bash
ollama serve
```

Qwen 模型应已下载：
```bash
ollama pull qwen:8b
```

## Dify 集成步骤

### 步骤 1: 打开 Dify 工作室

1. 登录 Dify
2. 进入任意一个工作流或应用

### 步骤 2: 添加自定义工具

1. 点击左侧菜单 "工具" 或 "插件"
2. 选择 "新建工具" → "API"
3. 选择 "From API URL" 或 "API 集成"

### 步骤 3: 配置工具信息

#### 基本信息

- **工具名称**: `AI Agent Architect`
- **工具描述**: `根据自然语言需求自动生成 Dify DSL 工作流配置`

#### API 配置

- **API 端点**: `http://localhost:8000/api/generate`
- **请求方法**: `POST`
- **认证类型**: `无` (None)

#### 输入参数

```json
{
  "type": "object",
  "required": ["requirement"],
  "properties": {
    "requirement": {
      "type": "string",
      "title": "智能体需求",
      "description": "用自然语言描述要创建的智能体功能",
      "example": "我需要一个智能体，能根据用户输入的查询，调用搜索工具并返回结果。"
    },
    "save_to_file": {
      "type": "boolean",
      "title": "保存到文件",
      "description": "是否保存生成的 DSL 到文件",
      "default": false
    }
  }
}
```

#### 输出响应

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "description": "状态: success 或 error"
    },
    "dsl": {
      "type": "object",
      "description": "生成的 Dify DSL 配置"
    },
    "is_valid": {
      "type": "boolean",
      "description": "DSL 是否有效"
    },
    "errors": {
      "type": "array",
      "description": "错误列表"
    },
    "warnings": {
      "type": "array",
      "description": "警告列表"
    }
  }
}
```

### 步骤 4: 测试工具

1. 点击 "测试" 按钮
2. 输入测试需求，例如：
   ```
   我需要一个文本分类智能体，输入字段是 'text'，输出字段是 'category'
   ```
3. 点击 "运行" 检查返回结果

### 步骤 5: 在工作流中使用

#### 方式 1: 在工作流中添加工具节点

1. 创建新的工作流或打开现有工作流
2. 点击 "添加节点" → "工具"
3. 选择 "AI Agent Architect"
4. 配置输入参数（requirement）
5. 运行工作流获取生成的 DSL

#### 方式 2: 在提示词中引用

在 LLM 节点的提示词中使用工具调用：

```
请根据以下需求帮我设计一个 Dify 工作流：

{{requirement}}

然后使用 "AI Agent Architect" 工具生成相应的 DSL 配置。
```

## 使用示例

### 示例 1: 文本分类工作流

**输入需求**：
```
我需要一个智能体，能对用户输入的文本进行情感分类（正面、中立、负面）。
输入字段是 'text'，输出字段是 'sentiment'。
```

**生成的 DSL**：
```json
{
  "version": "0.1",
  "nodes": [
    {
      "id": "input",
      "type": "input",
      "outputs": ["llm_classify"]
    },
    {
      "id": "llm_classify",
      "type": "llm",
      "config": {
        "model": "qwen:8b",
        "prompt": "请对以下文本进行情感分类："
      },
      "inputs": ["input"],
      "outputs": ["output"]
    },
    {
      "id": "output",
      "type": "output",
      "inputs": ["llm_classify"]
    }
  ]
}
```

### 示例 2: 数据查询工作流

**输入需求**：
```
创建一个多步骤智能体：
1) 接收用户的数据查询请求
2) LLM 理解查询意图
3) 调用数据库查询工具
4) 对结果进行处理
5) 返回最终结果

输入字段：query
输出字段：result
```

## 导入生成的 DSL

### 方式 1: 复制粘���

1. 复制生成的 DSL JSON
2. 在 Dify 中创建新的工作流或应用
3. 使用 "导入" 功能粘贴 DSL

### 方式 2: 从文件导入

如果启用了 `save_to_file` 选项：

1. DSL 将保存到 `output/generated_dsl.json`
2. 在 Dify 中使用 "导入" → "从文件选择"
3. 选择生成的 DSL 文件

## API 端点参考

### 1. 生成 DSL

**POST** `/api/generate`

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "我需要一个文本分类智能体",
    "save_to_file": true
  }'
```

### 2. 验证 DSL

**POST** `/api/validate`

```bash
curl -X POST "http://localhost:8000/api/validate" \
  -H "Content-Type: application/json" \
  -d '{"dsl": {...}}'
```

### 3. 优化 DSL

**POST** `/api/optimize`

```bash
curl -X POST "http://localhost:8000/api/optimize" \
  -H "Content-Type: application/json" \
  -d '{"dsl": {...}}'
```

### 4. 健康检查

**GET** `/api/health`

```bash
curl http://localhost:8000/api/health
```

## 故障排除

### 问题 1: Dify 无法连接到服务

**症状**: `连接被拒绝` 或 `超时`

**解决方案**:
1. 确保 AI Agent Architect 服务已启动
2. 检查防火墙设置
3. 如果在不同机器，使用实际 IP 地址而不是 `localhost`

### 问题 2: 模型响应缓慢

**症状**: 工具执行时间过长

**解决方案**:
1. 检查 Ollama 服务状态
2. 增加超时时间（在 `config.yaml` 中修改 `timeout`）
3. 简化需求描述

### 问题 3: 生成的 DSL 无效

**症状**: `is_valid` 为 false，包含错误

**解决方案**:
1. 检查返回的 `errors` 列表
2. 修改需求描述，更清楚地说明工作流
3. 使用示例中的需求格式

## 后续步骤

1. **编辑生成的工作流**: 在 Dify 中进一步调整和优化
2. **测试工作流**: 使用 Dify 的测试功能验证工作流
3. **部署**: 将完成的智能体部署到生产环境
4. **监控**: 使用 Dify 的监控工具跟踪性能

## 更多帮助

- Dify 官方文档: https://docs.dify.ai
- AI Agent Architect 项目: https://github.com/aarongao10002-gif/aaron
