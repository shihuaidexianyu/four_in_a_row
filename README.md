# 四子棋
复现

Van Opheusden, B., Kuperwajs, I., Galbiati, G., Bnaya, Z., Li, Y., & Ma, W. J. (2023). Expertise increases planning depth in human gameplay. Nature, 618(7967), 1000-1005.

## 工具链与技术栈
uv

## 项目结构
- 游戏规则程序化与裁判代码 （游戏本体）
    - 抽象出通用接口（ai和人类都可以使用）
    - 结构化游戏日志收集
- agent代码（ai）
    - 待定
- web游玩界面（web可视化游玩+数据收集）
    - 完成人类方输入
    - 对局数据实时可视化


## 游戏规则
在一个横向排布的4*9的棋盘里，黑方先执棋，黑白双方交替落子，直至有一方有4颗棋子连成一条线（水平，竖直，左上到右下，右上到左下）视为胜利，即游戏结束。

