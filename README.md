**<font style="color:#0d0d0d;">一．项目简介：</font>**

**<font style="color:#0d0d0d;">该项目是一个毕业设计项目，</font>**<font style="color:#0d0d0d;">基于Django框架的个性化推荐系统，采用基于用户的协同过滤算法，实现电影相似度计算与Top-N推荐</font>

**<font style="color:#0d0d0d;">二．技术实现：</font>**

1. <font style="color:#0d0d0d;">  </font>**<font style="color:#0d0d0d;">数据层</font>**
    - <font style="color:#0d0d0d;">调用豆瓣</font><font style="color:#0d0d0d;">API</font><font style="color:#0d0d0d;">获取</font><font style="color:#0d0d0d;">10,000+</font><font style="color:#0d0d0d;">条电影元数据（标题</font><font style="color:#0d0d0d;">/</font><font style="color:#0d0d0d;">评分</font><font style="color:#0d0d0d;">/</font><font style="color:#0d0d0d;">类型），使用</font><font style="color:#0d0d0d;">SQLite</font><font style="color:#0d0d0d;">进行本地数据存储</font>
    - <font style="color:#0d0d0d;">通过</font><font style="color:#0d0d0d;">Pandas</font><font style="color:#0d0d0d;">清洗数据，处理缺失值及异常评分数据等等。</font>
2. **<font style="color:#0d0d0d;">算法层</font>**
    - <font style="color:#0d0d0d;">构建用户</font><font style="color:#0d0d0d;">-</font><font style="color:#0d0d0d;">电影评分矩阵，采用皮尔逊相关系数计算相似度；</font>
    - <font style="color:#0d0d0d;">实现</font><font style="color:#0d0d0d;">Top-5</font><font style="color:#0d0d0d;">推荐逻辑，针对新用户提供基于热门电影的冷启动方案。</font>
3. **<font style="color:#0d0d0d;">工程局限</font>**
    - <font style="color:#0d0d0d;">未引入缓存机制，推荐响应延迟为</font><font style="color:#0d0d0d;">15~20s+</font><font style="color:#0d0d0d;">；</font>
    - <font style="color:#0d0d0d;">采用同步计算模式，未实现算法模块的异步优化。</font>

项目演示：

![](https://cdn.nlark.com/yuque/0/2025/png/38811268/1741155195279-657bbfcc-c399-4760-be69-9e95956f25d1.png)

个人中心页面展示

![](https://cdn.nlark.com/yuque/0/2025/png/38811268/1741155229760-3983502c-534d-4501-8591-9417932d2d9f.png)

用户评分页面展示

![](https://cdn.nlark.com/yuque/0/2025/png/38811268/1741155274176-fb353a33-32e4-40e4-82d2-accda28c786f.png)

![](https://cdn.nlark.com/yuque/0/2025/png/38811268/1741155322084-7b46634c-c708-45e1-b90b-f52c244335ec.png)

推荐成果页面展示



