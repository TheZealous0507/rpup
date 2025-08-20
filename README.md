第三题-智享生活
#
在快节奏的现代生活中，追求健康饮食常常面临两大难题：​​“吃什么才健康？”​​ 和 ​​“怎么吃才合适？”​​ 传统的饮食规划往往复杂繁琐，食谱选择难以精准匹配个人需求与目标（如减脂、增肌、疾病管理等），卡路里计算更是费时费力。为了“智享生活”，我们团队决定开发一个健康饮食追踪系统———FoodApp。

FoodApp是一个基于Django的健康饮食追踪系统，帮助用户记录饮食、运动和健康数据，实现个人健康目标。

## 目录
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [安装与配置](#安装与配置)
- [运行指南](#运行指南)
- [访问方式](#访问方式)
- [部署指南](#部署指南)
- [安全提示](#安全提示)

## 功能特性

### 1. 用户管理
- 用户注册与登录
- 个人资料管理
- 身体指标设置
- 头像个性化设置

### 2. 饮食追踪
- 食物数据库查询：提供丰富的食物营养成分数据库，支持模糊搜索
- 餐食记录添加：支持三餐记录（早餐、午餐、晚餐）及加餐记录
- 营养成分分析：自动计算每餐及每日的营养成分摄入（蛋白质、碳水化合物、脂肪等）
- 卡路里计算：基于食物分量自动计算卡路里摄入量
- 饮食图表统计：提供可视化图表展示饮食摄入趋势和营养均衡情况
- 饮食建议：根据用户目标提供个性化饮食建议

### 3. 运动管理
- 运动项目记录
- 卡路里消耗计算
- 运动时长追踪

### 4. 健康监控
- 体重变化跟踪
- 身体成分分析
- 睡眠质量记录
- 饮水情况追踪

### 5. 社交功能
- 群组创建与管理
- 健康挑战参与
- 活动分享
- 群组内消息交流

## 技术栈

- **后端框架**: Django 4.2
- **数据库**: MySQL
- **前端技术**: HTML, CSS, JavaScript
- **数据库设计**: 包含用户、食物、餐食记录、运动、目标等14个核心数据表

## 项目结构

```
Food/
├── Food/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── FoodApp/
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   ├── templates/
│   │   └── FoodApp/
│   ├── apps.py
│   ├── urls.py
│   └── views.py
├── database.sql
├── manage.py
└── requirements.txt
```

## 安装与配置

1. 环境要求：
   - Python 3.8+
   - MySQL 5.7+

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 数据库配置：
   - 在MySQL中创建数据库
   - 修改`Food/settings.py`中的数据库配置信息
   - 执行`database.sql`脚本初始化数据库表

## 运行指南

1. 开发环境运行：
   ```bash
   python manage.py runserver
   ```
   
2. 默认访问地址：
   - 本地开发服务器：http://127.0.0.1:8000/

## 访问方式

本项目为Web应用程序，部署后可通过浏览器访问。目前项目已在以下服务器部署：

- 演示服务器：http://115.190.61.135:8000/
- 用户名：admin
- 密码：123456

本地运行方式：

1. 按照[安装与配置](#安装与配置)部分完成环境搭建
2. 按照[运行指南](#运行指南)启动服务
3. 在浏览器中访问 http://127.0.0.1:8000/ 查看应用

如需部署到生产环境，请参考[部署指南](#部署指南)部分。

## 部署指南

1. 生产环境配置：
   - 修改`Food/settings.py`中的配置：
     ```python
     DEBUG = False
     ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']  # 替换为你的域名
     SECRET_KEY = 'your-new-secret-key'  # 使用新的密钥替换默认密钥
     ```
   
2. 数据库配置：
   - 在生产环境中，建议使用环境变量配置数据库连接信息：
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': os.environ.get('DB_NAME'),
             'USER': os.environ.get('DB_USER'),
             'PASSWORD': os.environ.get('DB_PASSWORD'),
             'HOST': os.environ.get('DB_HOST'),
             'PORT': os.environ.get('DB_PORT', '3306'),
         }
     }
     ```

3. 静态文件收集：
   ```bash
   python manage.py collectstatic
   ```

4. 使用WSGI服务器部署（如Gunicorn）：
   ```bash
   gunicorn Food.wsgi:application --bind 0.0.0.0:8000
   ```

5. 建议使用Nginx作为反向代理服务器处理静态文件和SSL证书。

## 安全提示

- 生产环境中请修改默认的SECRET_KEY
- 数据库密码等敏感信息应使用环境变量配置
- 生产环境中应将DEBUG设置为False
- 合理配置ALLOWED_HOSTS

