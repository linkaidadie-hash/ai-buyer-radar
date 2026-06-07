"""
Requirement Guard 测试套件
v0.3.2 M4: 覆盖 ≥15 个测试

测试覆盖：
- 必须功能存在
- 禁止功能拒绝
- 未定义功能告警
- Spec 加载失败
- 空 Spec
- 多项目 Spec
"""

import pytest
import tempfile
import os
from pathlib import Path

from core.guards.requirement_guard import (
    RequirementGuard,
    RequirementSpec,
    ValidationResult,
    ValidationLevel,
    ValidationCode,
)
from core.guards.task_spec import Task, TaskWithSpec


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def guard():
    return RequirementGuard()


@pytest.fixture
def spec_path():
    """临时 YAML Spec 文件"""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(
            "project: test-project\n"
            "version: '1.0'\n"
            "description: 测试项目\n"
            "must_have:\n"
            "  - 订单创建\n"
            "  - 订单审批\n"
            "  - 图片上传\n"
            "must_not_have:\n"
            "  - CRM\n"
            "  - ERP\n"
            "  - 财务系统\n"
            "entities:\n"
            "  - order\n"
            "  - customer\n"
            "critical_flows:\n"
            "  - create_order\n"
            "  - approve_order\n"
        )
        name = f.name
    yield name
    os.unlink(name)


@pytest.fixture
def empty_spec_path():
    """空 Spec 文件"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("")
        name = f.name
    yield name
    os.unlink(name)


@pytest.fixture
def invalid_spec_path():
    """无效 Spec（缺少 project 字段）"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("version: '1.0'\nmust_have: []\nmust_not_have: []")
        name = f.name
    yield name
    os.unlink(name)


# ============================================================
# M1: Spec 加载测试
# ============================================================

class TestLoadSpec:
    def test_load_valid_spec(self, guard, spec_path):
        """能够加载有效的 example_embroidery.yaml"""
        spec = guard.load_spec(spec_path)
        assert spec.project == "test-project"
        assert spec.version == "1.0"
        assert "订单创建" in spec.must_have
        assert "CRM" in spec.must_not_have

    def test_load_nonexistent_file_raises(self, guard):
        """Spec 文件不存在时抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            guard.load_spec("nonexistent/path/spec.yaml")

    def test_load_empty_file_raises(self, guard, empty_spec_path):
        """空 Spec 文件抛出 ValueError"""
        with pytest.raises(ValueError):
            guard.load_spec(empty_spec_path)

    def test_load_invalid_spec_raises(self, guard, invalid_spec_path):
        """缺少 project 字段时抛出 ValueError"""
        with pytest.raises(ValueError, match="Missing 'project'"):
            guard.load_spec(invalid_spec_path)

    def test_spec_cache(self, guard, spec_path):
        """同一路径多次 load_spec 返回同一实例（缓存）"""
        spec1 = guard.load_spec(spec_path)
        spec2 = guard.load_spec(spec_path)
        assert spec1 is spec2


# ============================================================
# M2: validate_feature 测试
# ============================================================

class TestValidateFeature:
    def test_forbidden_feature_rejected(self, guard, spec_path):
        """能够判断 CRM 属于 forbidden"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "CRM")
        assert result.passed is False
        assert result.level == ValidationLevel.ERROR
        assert result.code == ValidationCode.FORBIDDEN_FEATURE
        assert "CRM" in result.message

    def test_forbidden_feature_case_insensitive(self, guard, spec_path):
        """大小写不敏感：crm 也会被拒绝"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "crm")
        assert result.passed is False
        assert result.code == ValidationCode.FORBIDDEN_FEATURE

    def test_forbidden_feature_partial_match(self, guard, spec_path):
        """模糊匹配：包含 ERP 也会被拒绝"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "ERP财务模块")
        assert result.passed is False
        assert result.code == ValidationCode.FORBIDDEN_FEATURE

    def test_required_feature_accepted(self, guard, spec_path):
        """能够判断 订单审批 属于 required"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "订单审批")
        assert result.passed is True
        assert result.level == ValidationLevel.OK
        assert result.code == ValidationCode.OK

    def test_undefined_feature_warns(self, guard, spec_path):
        """未定义功能给出警告（不阻止）"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "数据分析")
        assert result.passed is True
        assert result.level == ValidationLevel.WARNING
        assert result.code == ValidationCode.UNDEFINED_FEATURE

    def test_undefined_feature_partial_match_warns(self, guard, spec_path):
        """未定义功能的模糊匹配也警告"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "订单")
        assert result.passed is True
        assert result.level == ValidationLevel.WARNING

    def test_empty_feature_name(self, guard, spec_path):
        """空功能名返回 UNDEFINED_FEATURE 警告"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "")
        assert result.passed is True
        assert result.level == ValidationLevel.WARNING

    def test_whitespace_feature_name(self, guard, spec_path):
        """带空格的功能名能正常处理"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_feature(spec, "  订单创建  ")
        # 会被 strip，然后匹配到订单创建
        assert result.passed is True


# ============================================================
# M2: validate_change 测试
# ============================================================

class TestValidateChange:
    def test_change_with_forbidden_rejected(self, guard, spec_path):
        """变更描述包含禁止功能时被拒绝"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_change(spec, "添加ERP模块到系统中")
        assert result.passed is False
        assert result.code == ValidationCode.FORBIDDEN_FEATURE

    def test_change_with_required_accepted(self, guard, spec_path):
        """变更描述包含必须功能时通过"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_change(spec, "实现订单审批流程")
        assert result.passed is True
        assert result.level == ValidationLevel.OK

    def test_change_undefined_warns(self, guard, spec_path):
        """变更描述不在 Spec 中时警告"""
        spec = guard.load_spec(spec_path)
        result = guard.validate_change(spec, "添加用户反馈功能")
        assert result.passed is True
        assert result.level == ValidationLevel.WARNING


# ============================================================
# M3: Task 接入测试
# ============================================================

class TestTaskWithSpec:
    def test_task_create_with_spec(self, guard, spec_path):
        """Task 关联 RequirementSpec"""
        tws = TaskWithSpec(guard)
        task = tws.create(
            task_id="task-001",
            title="添加订单审批功能",
            description="实现订单审批流程",
            spec_path=spec_path,
        )
        assert task.spec is not None
        assert task.spec.project == "test-project"

    def test_task_validate_forbidden_rejected(self, guard, spec_path):
        """Task 标题包含禁止功能被拒绝"""
        tws = TaskWithSpec(guard)
        task = tws.create(
            task_id="task-002",
            title="添加CRM模块",
            spec_path=spec_path,
        )
        errors = tws.validate_task(task)
        assert len(errors) == 1
        assert errors[0].code == ValidationCode.FORBIDDEN_FEATURE

    def test_task_validate_allowed_pass(self, guard, spec_path):
        """Task 标题为允许功能时通过"""
        tws = TaskWithSpec(guard)
        task = tws.create(
            task_id="task-003",
            title="实现图片上传功能",
            spec_path=spec_path,
        )
        errors = tws.validate_task(task)
        assert len(errors) == 0

    def test_task_without_spec(self):
        """Task 未关联 Spec 时 validate_task 返回空"""
        tws = TaskWithSpec()
        task = Task(id="task-004", title="任意任务")
        errors = tws.validate_task(task)
        assert errors == []


# ============================================================
# M4: 多 Spec / 边界测试
# ============================================================

class TestMultiSpec:
    def test_multiple_specs_independent(self, guard):
        """多项目 Spec 互不影响"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "project: project-a\n"
                "version: '1.0'\n"
                "must_have:\n"
                "  - 功能A\n"
                "must_not_have:\n"
                "  - 禁止A\n"
            )
            path_a = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "project: project-b\n"
                "version: '1.0'\n"
                "must_have:\n"
                "  - 功能B\n"
                "must_not_have:\n"
                "  - 禁止B\n"
            )
            path_b = f.name

        try:
            spec_a = guard.load_spec(path_a)
            spec_b = guard.load_spec(path_b)

            assert spec_a.project == "project-a"
            assert spec_b.project == "project-b"

            # 功能A 在 project-a 是必须，在 project-b 未定义
            result_a = guard.validate_feature(spec_a, "功能A")
            assert result_a.code == ValidationCode.OK

            result_b = guard.validate_feature(spec_b, "功能A")
            assert result_b.code == ValidationCode.UNDEFINED_FEATURE

            # 禁止A 在 project-a 是禁止
            result_forbid = guard.validate_feature(spec_a, "禁止A")
            assert result_forbid.code == ValidationCode.FORBIDDEN_FEATURE
        finally:
            os.unlink(path_a)
            os.unlink(path_b)


class TestEdgeCases:
    def test_spec_with_no_must_have(self, guard):
        """Spec 没有 must_have 时，validate_feature 对未定义功能仍警告"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "project: empty-project\n"
                "version: '1.0'\n"
                "must_have: []\n"
                "must_not_have:\n"
                "  - 禁止项\n"
            )
            path = f.name
        try:
            spec = guard.load_spec(path)
            result = guard.validate_feature(spec, "任意功能")
            assert result.code == ValidationCode.UNDEFINED_FEATURE
        finally:
            os.unlink(path)

    def test_spec_with_no_must_not_have(self, guard):
        """Spec 没有 must_not_have 时，允许所有功能"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "project: open-project\n"
                "version: '1.0'\n"
                "must_have:\n"
                "  - 必须项\n"
                "must_not_have: []\n"
            )
            path = f.name
        try:
            spec = guard.load_spec(path)
            result = guard.validate_feature(spec, "CRM")
            assert result.code == ValidationCode.UNDEFINED_FEATURE
        finally:
            os.unlink(path)

    def test_validate_task_description_only(self, guard, spec_path):
        """Task 只有 description 没有 title 时也能校验"""
        tws = TaskWithSpec(guard)
        task = tws.create(
            task_id="task-005",
            title="任务标题",
            description="在描述中添加ERP功能",
            spec_path=spec_path,
        )
        errors = tws.validate_task(task)
        assert len(errors) == 1
        assert errors[0].code == ValidationCode.FORBIDDEN_FEATURE


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])