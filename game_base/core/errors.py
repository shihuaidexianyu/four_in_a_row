"""规则层和调度层共用的领域错误。"""


class GameError(Exception):
    """所有游戏相关异常的基类。"""


class InvalidMoveError(GameError):
    """当动作无法应用到当前状态时抛出。"""
