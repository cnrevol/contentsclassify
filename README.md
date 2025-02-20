# Content Classification System

A full-stack application for email and content classification using Python, Django, React, and LLM integration.

## Features

1. Data Input
   - Upload text and email files through web interface
   - Connect to email server for receiving emails
   - Manual text input

2. Backend Processing
   - File type recognition
   - Content classification using LLM
   - Post-processing and database storage

3. Data Output
   - Real-time processing feedback
   - Classification results display

## Setup Instructions

### Backend Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
   Create a `.env` file in the root directory with:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
LLM_API_KEY=your-llm-api-key
```

venv\Scripts\activate


4. Run migrations:
```bash
python manage.py migrate
```

5. Start Django server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

## Project Structure

```
project/
├── backend/
│   ├── content_classifier/
│   ├── email_processor/
│   ├── file_processor/
│   └── api/
├── frontend/
│   ├── src/
│   └── public/
├── config/
│   └── classification_rules/
└── docs/
```

## Configuration

Classification rules and data type definitions are stored in XML format in the `config/classification_rules` directory. 



1. 后端服务运行在 http://localhost:8000
Django 管理界面：http://localhost:8000/admin
API 端点：http://localhost:8000/api/
管理员账号：
用户名：admin
密码：admin123
前端服务运行在 http://localhost:3000
登录页面：http://localhost:3000/login
注册页面：http://localhost:3000/register
主面板：http://localhost:3000/
你可以通过以下方式访问应用：
1. 在浏览器中打开 http://localhost:3000 访问前端应用
使用上述管理员账号登录系统
在 http://localhost:8000/admin 访问Django管理界面
如果你需要停止服务，可以在各自的终端窗口中按 Ctrl+C。


https://ibm.monday.com/boards/8197810446/pulses/8275874082
https://app.napkin.ai/


改图，outlook调用服务。

1. 上传数据，后端分层处理。
   1. 决策树。
   2. 
2. 