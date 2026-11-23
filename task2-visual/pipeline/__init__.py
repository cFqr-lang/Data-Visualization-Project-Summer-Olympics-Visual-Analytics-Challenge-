"""任务二数据管线：只读原始数据，产出聚合 JSON 与全队统一底表。

约定：
- 不修改 data/ 下任何文件，也不改写任务一的口径契约；
- 任务一产物（contracts/caliber_spec.md、data/processed/）就绪后，只需替换
  `common.load_records` 的实现，其余指标与图表 JSON 保持不变。
"""

__all__ = ["common", "metrics", "build"]
__version__ = "1.0.0"
