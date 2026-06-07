"""
Requirement Guard - v0.3.2 MVP
确定性规则驱动，防范需求漂移

职责：
- 加载 Requirement Spec（YAML）
- 校验 Task / Change / Feature 是否在范围内
- 拒绝 must_not_have（禁止功能）
- 警告 UNDEFINED_FEATURE（未定义功能）
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

import yaml


class ValidationLevel(Enum):
    """校验结果级别"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class ValidationCode(Enum):
    """校验错误码"""
    OK = "OK"
    FORBIDDEN_FEATURE = "FORBIDDEN_FEATURE"      # 在 must_not_have 中
    REQUIRED_FEATURE_MISSING = "REQUIRED_FEATURE_MISSING"  # 在 must_have 中但不存在
    UNDEFINED_FEATURE = "UNDEFINED_FEATURE"      # 未在 Spec 中定义


@dataclass
class ValidationResult:
    """校验结果"""
    passed: bool
    level: ValidationLevel
    code: ValidationCode
    message: str
    feature: str

    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.code.value} | {self.feature} | {self.message}"


@dataclass
class RequirementSpec:
    """需求规范"""
    project: str
    version: str
    description: str = ""
    must_have: List[str] = field(default_factory=list)
    must_not_have: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    critical_flows: List[str] = field(default_factory=list)
    _spec_path: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "RequirementSpec":
        """从字典加载"""
        return cls(
            project=data.get("project", ""),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            must_have=data.get("must_have", []),
            must_not_have=data.get("must_not_have", []),
            entities=data.get("entities", []),
            critical_flows=data.get("critical_flows", []),
        )


class RequirementGuard:
    """
    Requirement Guard 引擎

    使用方式：
        guard = RequirementGuard()
        spec = guard.load_spec("requirements/example_embroidery.yaml")

        result = guard.validate_feature(spec, "CRM")
        # result.passed=False, result.level=ERROR, result.code=FORBIDDEN_FEATURE

        result = guard.validate_feature(spec, "订单审批")
        # result.passed=True, result.level=OK, result.code=OK
    """

    def __init__(self):
        self._spec_cache: dict[str, RequirementSpec] = {}

    def load_spec(self, spec_path: str) -> RequirementSpec:
        """
        加载 Requirement Spec

        Args:
            spec_path: YAML 文件路径

        Returns:
            RequirementSpec 实例

        Raises:
            FileNotFoundError: Spec 文件不存在
            ValueError: Spec 格式无效
        """
        path = Path(spec_path)

        if not path.exists():
            raise FileNotFoundError(f"Requirement Spec not found: {spec_path}")

        # 缓存检查
        if str(path) in self._spec_cache:
            return self._spec_cache[str(path)]

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty or invalid YAML: {spec_path}")

        if "project" not in data:
            raise ValueError(f"Missing 'project' field in: {spec_path}")

        spec = RequirementSpec.from_dict(data)
        spec._spec_path = str(path)

        self._spec_cache[str(path)] = spec
        return spec

    def validate_feature(self, spec: RequirementSpec, feature: str) -> ValidationResult:
        """
        校验单个功能是否合规

        Args:
            spec: RequirementSpec 实例
            feature: 功能名称

        Returns:
            ValidationResult
        """
        feature_normalized = feature.strip()

        # 1. 检查是否在 must_not_have（禁止功能）
        for forbidden in spec.must_not_have:
            if self._matches(feature_normalized, forbidden):
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.ERROR,
                    code=ValidationCode.FORBIDDEN_FEATURE,
                    message=f"'{feature}' 属于禁止功能 (must_not_have)",
                    feature=feature_normalized,
                )

        # 2. 检查是否在 must_have（必须功能）
        for required in spec.must_have:
            if self._matches(feature_normalized, required):
                return ValidationResult(
                    passed=True,
                    level=ValidationLevel.OK,
                    code=ValidationCode.OK,
                    message=f"'{feature}' 是必须功能 (must_have)",
                    feature=feature_normalized,
                )

        # 3. 未在任何列表中 → 警告（不阻止）
        return ValidationResult(
            passed=True,
            level=ValidationLevel.WARNING,
            code=ValidationCode.UNDEFINED_FEATURE,
            message=f"'{feature}' 未在 Requirement Spec 中定义",
            feature=feature_normalized,
        )

    def validate_task(
        self,
        spec: RequirementSpec,
        task_title: str,
        task_description: str = "",
    ) -> List[ValidationResult]:
        """
        校验 Task 是否合规

        检查 task_title 和 task_description 中是否包含禁止功能

        Args:
            spec: RequirementSpec 实例
            task_title: 任务标题
            task_description: 任务描述（可选）

        Returns:
            ValidationResult 列表
        """
        results = []

        # 检查标题
        title_result = self._check_text(spec, task_title, "task_title")
        if title_result.level == ValidationLevel.ERROR:
            results.append(title_result)

        # 检查描述
        if task_description:
            desc_result = self._check_text(spec, task_description, "task_description")
            if desc_result.level == ValidationLevel.ERROR:
                results.append(desc_result)

        return results

    def validate_change(
        self,
        spec: RequirementSpec,
        change_description: str,
    ) -> ValidationResult:
        """
        校验变更请求是否合规

        Args:
            spec: RequirementSpec 实例
            change_description: 变更描述

        Returns:
            ValidationResult
        """
        return self._check_text(spec, change_description, "change")

    # ─── 私有方法 ───────────────────────────────────────────

    def _check_text(
        self,
        spec: RequirementSpec,
        text: str,
        context: str,
    ) -> ValidationResult:
        """检查文本中是否包含禁止功能"""
        text_normalized = text.strip()

        # 先检查禁止功能
        for forbidden in spec.must_not_have:
            if self._matches(text_normalized, forbidden):
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.ERROR,
                    code=ValidationCode.FORBIDDEN_FEATURE,
                    message=f"context='{context}': '{text}' 包含禁止功能 '{forbidden}'",
                    feature=text_normalized,
                )

        # 检查是否在 must_have 中
        for required in spec.must_have:
            if self._matches(text_normalized, required):
                return ValidationResult(
                    passed=True,
                    level=ValidationLevel.OK,
                    code=ValidationCode.OK,
                    message=f"context='{context}': '{text}' 包含必须功能 '{required}'",
                    feature=text_normalized,
                )

        # 未定义 → 警告
        return ValidationResult(
            passed=True,
            level=ValidationLevel.WARNING,
            code=ValidationCode.UNDEFINED_FEATURE,
            message=f"context='{context}': '{text}' 未在 Spec 中定义",
            feature=text_normalized,
        )

    @staticmethod
    def _matches(text: str, keyword: str) -> bool:
        """
        模糊匹配：检查 text 是否包含 keyword（大小写不敏感）

        Args:
            text: 待检查文本
            keyword: 关键词

        Returns:
            True if text contains keyword (case-insensitive)
        """
        return keyword.lower() in text.lower()