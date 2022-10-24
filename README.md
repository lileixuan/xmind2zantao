## Xmind2Zantao

[![PyPI](https://img.shields.io/pypi/v/xmind2zantao.svg)](https://pypi.org/project/xmind2zantao/)

### 规则
**测试用例定义:**

![测试用例标记](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/测试用例标记.png)

**前置条件:**

![前置条件](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/前置条件.png)

**输出概览:**

![输出预览](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/输出预览.png)

### 详细说明

1. 优先级标记的节点，或者以`P-`和`N-`开头的节点，作为测试用例的标题，即测试用例开始。
2. 用例标题后的节点为用例步骤，用例步骤后面的节点为预期结果。
3. 用例标题之前的节点，拼接组成`模块`属性。
   1. 模块以`/`开始
   2. 如果标题之前的节点中定义了禅道中的真实模块（以模块ID结尾：`/云运营/账单/平台管理/快照账单汇总(#4086)`），则直接使用。
4. 使用`笔记(note)`作为前置条件。
5. 以`叹号(!)`开头的节点将被忽略。
6. 自由主题会被忽略，不进行转换


**下载示例Xmind文件:**

- [xmind2zantao.xmind](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/xmind2zantao.xmind)

### 附加功能（需要后台启用相关配置）

预览中查看每个用例的模块在禅道是否存在。

![禅道模块提示](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/禅道模块提示.png)

点击进入模块的树状展示页面，不存在的模块标红展示。

![禅道模块树展示](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/禅道模块树展示.png)


### 部署

安装软件包：
```shell
pip install xmind2zantao
```

1. 快速启动web服务

```shell
gunicorn xmind2zantao_web.application:app -p application.pid -b 0.0.0.0:8000 -w 4 -D
```
打开浏览器 输入正确的IP地址和端口来使用。

![首页](https://github.com/lileixuan/xmind2zantao/raw/main/xmind2zantao_web/static/guide/首页.png)


2. 启用禅道模块检查功能

启动服务时指定相应的环境变量即可

```python
gunicorn xmind2zantao_web.application:app -e ZANTAO_BASE_URL='http://127.0.0.1/zentao' -e ZANTAO_USERNAME=testuser -e ZANTAO_PASSWD='123456' -e ZANTAO_PRODUCT_ID=3 -p application.pid -b 0.0.0.0:8000 -w 4 -D
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