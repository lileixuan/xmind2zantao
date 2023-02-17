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


2. 启用禅道辅助功能

启用禅道辅助功能后，将会开启登录验证功能。用户可使用禅道账户登录，辅助功能的权限和登录账户一致。

启动服务时指定相应的环境变量即可

```python
gunicorn xmind2zantao_web.application:app -e ZANTAO_DEFAULT_EXECUTION_TYPE='功能测试' -e ZANTAO_BASE_URL='http://127.0.0.1/zentao' -e ZANTAO_PRODUCT_ID=1,3 -p application.pid -b 0.0.0.0:8000 -w 4 -D
```

需要的环境变量如下：
```python
# 禅道地址
ZANTAO_BASE_URL='http://127.0.0.1/zentao'

# 产品ID列表，逗号分割。如果配置了，将只能看到配置的产品。
ZANTAO_PRODUCT_ID=1,3
```

获取产品ID：

![产品ID](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/产品ID.png)


### 感谢

   参考：xmind2testlin xmindparser