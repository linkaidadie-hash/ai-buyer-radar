"""
Task + RequirementSpec 关联模块
v0.3.2 M3: Task 接入

在任务创建时支持 requirement_spec_id 字段，
关联 RequirementSpec，后续所有检查从 Spec 读取。

不修改现有 Scheduler / Executor / Runtime 行为。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from core.guards.requirement_guard import (
    RequirementGuard,
    RequirementSpec,
    ValidationResult,
)


@dataclass
class Task:
    """
    Task 模型（轻量，不碰现有数据库 schema）

    requirement_spec_id: Requirement Spec 文件路径（不含 .yaml 后缀可省略）
    """
    id: str
    title: str
    description: str = ""
    requirement_spec_id: Optional[str] = None   # Spec 文件路径
    _spec: Optional[RequirementSpec] = field(default=None, init=False, repr=False)

    def bind_spec(self, spec: RequirementSpec) -> None:
        """绑定 Spec"""
        self._spec = spec

    @property
    def spec(self) -> Optional[RequirementSpec]:
        return self._spec


class TaskWithSpec:
    """
    Task 创建辅助器

    使用方式：
        task = TaskWithSpec.create(
            id="task-001",
            title="添加CRM模块",
            description="为系统增加CRM客户管理功能",
            spec_path="requirements/example_embroidery",
        )
        # task.spec 可用
    """

    def __init__(self, guard: Optional[RequirementGuard] = None):
        self.guard = guard or RequirementGuard()

    def create(
        self,
        task_id: str,
        title: str,
        description: str = "",
        spec_path: Optional[str] = None,
    ) -> Task:
        """
        创建 Task 并绑定 Spec

        Args:
            task_id: 任务ID
            title: 任务标题
            description: 任务描述
            spec_path: Spec 文件路径（相对路径或绝对路径）

        Returns:
            Task 实例（已绑定 Spec）
        """
        task = Task(
            id=task_id,
            title=title,
            description=description,
            requirement_spec_id=spec_path,
        )

        if spec_path:
            # 自动解析路径
            resolved_path = self._resolve_spec_path(spec_path)
            spec = self.guard.load_spec(resolved_path)
            task.bind_spec(spec)

        return task

    def validate_task(self, task: Task) -> List[ValidationResult]:
        """
        校验 Task 是否合规

        Returns:
            ValidationResult 列表（仅包含 ERROR 级别的结果）
        """
        if not task.spec:
            return []

        results = self.guard.validate_task(
            spec=task.spec,
            task_title=task.title,
            task_description=task.description,
        )

        # 只返回 ERROR 级别的结果（禁止功能）
        return [r for r in results if r.level.value == "error"]

    @staticmethod
    def _resolve_spec_path(spec_path: str) -> str:
        """解析 Spec 路径"""
        path = Path(spec_path)
        if path.suffix == ".yaml":
            return str(path)
        return str(path.with_suffix(".yaml"))