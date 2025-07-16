
# AI助手 Web应用

一个现代化的AI助手Web应用，采用Flask后端和响应式前端设计。

## 功能特性

### 🎨 现代化界面
- 类似ChatGPT的对话界面设计
- 响应式布局，支持移动端
- 流畅的动画效果和交互体验
- 优雅的消息气泡设计

### 💬 智能对话
- 支持多轮对话
- 实时打字指示器
- 消息历史记录
- 字符计数和输入验证

### 🛠️ 技术特性
- Flask后端框架
- Bootstrap 5前端框架
- 现代化JavaScript（ES6+）
- RESTful API设计
- 错误处理和用户反馈

## 项目结构

```
llmweb/
├── app/
│   ├── __init__.py          # Flask应用初始化
│   ├── run.py              # 应用启动文件
│   ├── agent.py            # AI代理逻辑
│   ├── models/             # 数据模型
│   ├── routes/             # 路由定义
│   ├── static/             # 静态资源
│   │   ├── css/
│   │   │   ├── bootstrap.min.css
│   │   │   └── styles.css   # 自定义样式
│   │   └── js/
│   │       ├── bootstrap.bundle.min.js
│   │       └── custom.js    # 自定义JavaScript
│   └── templates/          # HTML模板
│       └── index.html      # 主页面
├── agent_/                 # RAG相关功能
├── README.md
└── .gitignore
```

## 安装和运行

### 环境要求
- Python 3.8+
- Flask
- LangChain
- OpenAI API Key

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd llmweb
```

2. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖
```bash
pip install flask langchain-openai python-dotenv
```

4. 设置环境变量
创建`.env`文件并添加：
```
LLM_MODELEND=your_openai_model_name
OPENAI_API_KEY=your_openai_api_key
```

5. 运行应用
```bash
cd app
python run.py
```

6. 访问应用
打开浏览器访问：`http://localhost:5000`

## 界面特性

### 响应式设计
- 桌面端：最大宽度800px的居中布局
- 移动端：全屏自适应布局
- 触摸友好的交互元素

### 用户体验
- **智能输入框**：自动调整高度，最大150px
- **字符计数**：实时显示剩余字符，颜色提示
- **快捷键支持**：
  - `Enter`：发送消息
  - `Shift + Enter`：换行
  - 双击输入框：清空内容
- **打字指示器**：显示AI正在思考
- **自动滚动**：新消息自动滚动到底部

### 视觉效果
- 渐变背景和阴影效果
- 流畅的CSS动画过渡
- 消息气泡的圆角设计
- 悬停效果和状态反馈

## API接口

### POST /
发送消息给AI助手

**请求体：**
```json
{
    "question": "用户输入的问题"
}
```

**响应：**
```json
{
    "status": "success",
    "response": "AI助手的回复"
}
```

## 自定义配置

### 修改样式
编辑 `app/static/css/styles.css` 文件中的CSS变量：
```css
:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    /* 更多颜色变量... */
}
```

### 添加功能
- 在 `app/static/js/custom.js` 中添加前端逻辑
- 在 `app/run.py` 中添加后端路由
- 在 `app/templates/index.html` 中修改页面结构

## 开发说明

### 代码组织
- **ChatApp类**：封装所有前端交互逻辑
- **模块化设计**：功能分离，易于维护
- **错误处理**：完善的异常捕获和用户提示
- **性能优化**：防抖、节流和内存管理

### 扩展建议
- 添加用户认证系统
- 实现对话历史持久化
- 支持文件上传和处理
- 集成更多AI模型选择
- 添加语音输入/输出功能

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**注意：** 请确保在使用前正确配置环境变量和API密钥。
