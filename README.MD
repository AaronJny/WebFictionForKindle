# Kindle网文助手

Kindle网文助手，支持从网络上下载网络小说，并推送到kindle上阅读。是为解决无法在kindle上方便阅读网文而编写的小项目。

请注意，此项目不提倡盗版阅读，只因为手机起点看书费眼，才萌生想法编写此项目。没有直接爬起点网站，是嫌起点反爬太多，太麻烦了（毕竟起点要面对那么多盗版网站的爬虫）。网文作者写书不易，有能力的朋友尽量支持一下。

推荐如下操作：选择一本想看的书xxx => 打开起点，找到xxx => 自动订阅 => 打开kindle网文助手，缓存xxx => 推送到kindle阅读

如果真的没有闲钱，也请注册一下起点的账号，加一下收藏，投一下免费的推荐票，为你喜欢的小说点赞。写手不易，且行且珍惜。

# 开发环境

- 后端　Python3 + Flask
- 前端　Vue.js + Element UI
- 数据库　MySQL
- 消息队列　RabbitMQ


# 启动项目

1.下载项目：

```git clone xxx```

2.切换到项目根目录下的src目录：

```cd WebFictionForKindle/src```

3.安装依赖环境：

```pip install -r requirements.txt```

4.修改`config.py`里的数据库参数和消息队列参数，与你的数据库和消息队列参数一致。

如果没有安装mysql和rabbitmq，可以通过docker安装，请参考：

https://hub.daocloud.io/repos/fa51c1d6-9dc2-49d9-91ac-4bbfc24a1bda

https://hub.daocloud.io/repos/abd7d091-dc5e-4f20-8267-d17d845c1c36

mysql请安装5.7版本。

5.使用数据库可视化软件(DBeaver,Navicat,Mysql Workbench等)连接数据库，创建名为`kindle_web_fiction`的数据库，字符集选择utf8mb4。

6.根据需求修改`gunicorn_config.py`中的配置（无特殊需求可以不修改）。

7.启动web服务：

```bash run_web.sh```

如果需要后台运行，可以使用screen或者nohup。这里举个使用screen后台运行web服务的例子：

首先，你需要安装screen，以debian为例：

```sudo apt-get install screen```

先创建一个screen：

```screen -S kindle_web```

`kindle_web`就是我们创建的这个screen的标识。

运行启动脚本:

```bash run_web.sh```

断开screen链接，让程序后台运行，输入快捷键`Ctrl+A+D`。

当需要重新连接到程序时，不需要重新创建screen，直接输入如下命令即可：

```screen -r kindle_web```

需要后台运行时，同样输入快捷键`Ctrl+A+D`即可。

8.启动爬虫服务：

```python3 run_spider.py```

后台运行的方法参考第7步，当然，你需要给新创建的screen一个新的标识，比如`kindle_spider`。

完成，接下来直接在web中访问主机名+端口号即可，默认[http://localhost:7777/](http://localhost:7777/),根据个人情况修改。


# 项目演示

待更新

# 前端项目

[AaronJny/web_fiction_for_kindle_front](https://github.com/AaronJny/web_fiction_for_kindle_front)

