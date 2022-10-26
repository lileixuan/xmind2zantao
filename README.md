## Xmind2Zantao

[![PyPI](https://img.shields.io/pypi/v/xmind2zantao.svg)](https://pypi.org/project/xmind2zantao/)

### 使用说明

[https://github.com/lileixuan/xmind2zantao/blob/main/xmind2zantao_web/static/guide/index.md](https://github.com/lileixuan/xmind2zantao/blob/main/xmind2zantao_web/static/guide/index.md)

### 部署

安装软件包：
```shell
pip install xmind2zantao
```

1. 快速启动web服务

```shell
gunicorn xmind2zantao_web.application:app -e ZANTAO_DEFAULT_EXECUTION_TYPE='功能测试' -p application.pid -b 0.0.0.0:8000 -w 4 -D
```
**环境变量：**

    `ZANTAO_DEFAULT_EXECUTION_TYPE` 如果指定了值，当用例类型为空的时候会只用该值替换。

打开浏览器，输入上面指定IP地址和端口来使用。

![首页](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/首页.png)


2. 启用禅道模块检查功能

启动服务时指定相应的环境变量即可

```python
gunicorn xmind2zantao_web.application:app -e ZANTAO_DEFAULT_EXECUTION_TYPE='功能测试' -e ZANTAO_BASE_URL='http://127.0.0.1/zentao' -e ZANTAO_USERNAME=testuser -e ZANTAO_PASSWD='123456' -e ZANTAO_PRODUCT_ID=3 -p application.pid -b 0.0.0.0:8000 -w 4 -D
```

需要的环境变量如下：
```python
# 禅道地址
ZANTAO_BASE_URL='http://127.0.0.1/zentao'
# 登录用户名
ZANTAO_USERNAME='xxx'
# 登录密码
ZANTAO_PASSWD='xxx'
# 产品ID
ZANTAO_PRODUCT_ID=3
```

获取产品ID：

![产品ID](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/产品ID.png)

**注意:** 目前只支持对一个产品的目录进行检查，如果有多个产品都是用，可以部署多个web服务来暂时解决。

### 感谢

   参考：xmind2testlin xmindparser