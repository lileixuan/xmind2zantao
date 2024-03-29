## Xmind2Zantao 使用说明

### 规则
**测试用例定义:**

![测试用例标记](测试用例标记.png)

**前置条件:**

![前置条件](前置条件.png)


**用例类型:**

![用例类型](用例类型.png)


### 详细说明

1. 优先级标记的节点，或者以`P-`和`N-`开头的节点，作为测试用例的标题，即测试用例开始。
2. 用例标题后的节点为用例步骤，用例步骤后面的节点为预期结果。
3. 用例标题之前的节点，拼接组成`模块`属性。
   1. 模块以`/`开始
   2. 如果标题之前的节点中定义了禅道中的真实模块（以模块ID结尾：`/云运营/账单/平台管理/快照账单汇总(#4086)`），则直接使用。
4. 使用`笔记(note)`作为前置条件。
5. 使用`标签(label)`作为用例类型，只有第一个标签生效。
6. 以`叹号(!)`开头的节点将被忽略。
7. 自由主题会被忽略，不进行转换


**下载示例Xmind文件:**

- [xmind2zantao.xmind](xmind2zantao.xmind)

### 使用说明

使用禅道账号登录

![登录](登录.png)

预览中查看每个用例的模块在禅道是否存在。

![预览](预览.png)

点击进入模块的树状展示页面，不存在的模块标红展示。

![禅道模块树展示](禅道模块树展示.png)

**注意：** 登录、模块检查和模块自动创建功能，需要后台启用相关配置