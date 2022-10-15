# GwentAI
## 项目简介
基于DQN的昆特牌策略学习，对游戏环境进行了建模，采用有模型强化学习，训练时让己方、对方两个agent使用相同的网络参数，同时使用二者产生的经验进行学习。

## 说明
* 游戏分辨率1680\*1050，无边框窗口。
* 只支持北方领域对阵北方领域（与巴巴对战，选最高难度）
* 程序运行时请勿遮挡检测区域

## 存在问题
数字识别做的很粗糙，可能导致输入的state产生错误。

## 相关链接
*   [动手学强化学习](https://github.com/boyu-ai/Hands-on-RL)
*   文章链接：[模板匹配](https://blog.csdn.net/qq_40344307/article/details/95111626?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522166528234016782248551181%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=166528234016782248551181&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~sobaiduend~default-4-95111626-null-null.142^v52^pc_rank_34_2,201^v3^control_1&utm_term=python%20cv%E6%A8%A1%E6%9D%BF%E5%8C%B9%E9%85%8D&spm=1018.2226.3001.4187)
