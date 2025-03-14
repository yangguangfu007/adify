# Adify Web Service

这是一个使用Flask创建的Web服务示例，包含API接口和MySQL数据库连接。

## 项目结构

```
adify/
|- app.py           # 应用入口
   api/
   |- api.py           # API路由和接口定义
   |- __init__.py      # Flask应用初始化
   db/
     |- db.py            # MySQL数据库工具类
     |- schema.sql       # 数据库结构和初始数据
  upload/
     |- uploadfile.py    # 文件上传到Minio工具类
     |- schema.sql       # 数据库结构和初始数据
```

## 安装依赖

```bash
pip install flask pymysql
```

## 数据库设置

1. 确保MySQL服务已启动
2. 执行schema.sql脚本创建数据库和表:
   ```
   mysql -u root -p < adify/db/schema.sql
   ```

## 运行应用

```bash
python -m app
```
服务将在 http://localhost:5000 启动

生产使用
```bash
   pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
   - `-w 4`：指定启动 4 个工作进程。
   - `-b 0.0.0.0:5000`：绑定到所有网络接口的 `5000` 端口。
   - `app:app`：第一个 `app` 是文件名（`app.py`），第二个 `app` 是 Flask 应用实例的名称。
   如果需要在后台启动，可以使用 `nohup` 或 `screen`：
   ```bash
   nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > gunicorn.log 2>&1 &
   ```

## API接口

1. 健康检查: `GET /api/health`
2. 