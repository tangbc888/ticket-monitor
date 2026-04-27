"""平台适配器包 - 提供平台工厂和注册表"""
from app.platforms.base import PlatformAdapter
from app.platforms.damai import DamaiAdapter
from app.platforms.maoyan import MaoyanAdapter
from app.platforms.funwandao import FunwandaoAdapter

# 平台适配器注册表
PLATFORM_ADAPTERS = {
    "damai": DamaiAdapter,
    "maoyan": MaoyanAdapter,
    "funwandao": FunwandaoAdapter,
}


def get_adapter(platform: str) -> PlatformAdapter:
    """根据平台名获取适配器实例

    Args:
        platform: 平台名称（damai/maoyan/funwandao）

    Returns:
        对应平台的适配器实例

    Raises:
        ValueError: 不支持的平台名称
    """
    adapter_cls = PLATFORM_ADAPTERS.get(platform)
    if not adapter_cls:
        raise ValueError(f"不支持的平台: {platform}")
    return adapter_cls()


def get_all_adapters() -> dict:
    """获取所有平台适配器实例

    Returns:
        字典，键为平台名称，值为适配器实例
    """
    return {name: cls() for name, cls in PLATFORM_ADAPTERS.items()}
