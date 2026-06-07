# Requirement Guard 设计文档

> v0.3.2 MVP — 确定性规则驱动，防范需求漂移

---

## 1. Guard 职责

**Requirement Guard** 在任务/变更/功能执行前，校验是否符合 Requirement Spec 定义的范围。

职责：
- 加载项目 `Requirement Spec`（YAML 格式）
- 校验 `Task` 是否关联了有效的 Spec
- 校验功能/变更是否落在 `must_have` 范围
- 校验功能/变更是否触犯 `must_not_have` 禁区
- 对未在 Spec 中定义的功能给出警告（不阻止）

---

## 2. 数据结构

### RequirementSpec

```python
class RequirementSpec:
    project: str              # 项目名称，如 "embroidery-order-system"
    version: str              # Spec 版本，如 "1.0"
    must_have: List[str]      # 必须功能列表
    must_not_have: List[str]  # 禁止功能列表
    entities: List[str]       # 核心实体（如 order/customer/factory）
    critical_flows: List[str] # 关键业务流程
```

### ValidationResult

```python
class ValidationResult:
    passed: bool
    level: str           # "error" | "warning" | "ok"
    code: str            # 错误码，如 "FORBIDDEN_FEATURE"
    message: str         # 人类可读描述
    feature: str         # 被检查的功能名
```

---

## 3. 校验流程

```
输入: feature_name / task_description

1. load_spec() — 加载 RequirementSpec
   ↓
2. check_forbidden(feature) — 是否在 must_not_have？
   → 是 → 返回 error，code="FORBIDDEN_FEATURE"
   ↓ 否
3. check_required(feature) — 是否在 must_have？
   → 是 → 返回 ok
   ↓ 否
4. check_undefined(feature) — 是否在任何列表中？
   → 否 → 返回 warning，code="UNDEFINED_FEATURE"
   → 是 → 返回 ok
```

---

## 4. 与 Runtime 集成点

### 集成时机（MVP 范围）

**M3: Task 接入**

- Task 创建时接受 `requirement_spec_id` 字段
- Task 执行前调用 `RequirementGuard.validate_task(task)` 校验
- 校验失败时：记录警告，不阻止执行（规则驱动，非强制）

### 后续扩展点（v0.3.2 之后，不在 MVP 范围）

- Scheduler 接入：在任务调度前校验
- Executor 接入：在执行前校验
- Spec Guard：校验 Spec 本身质量
- Architecture Guard：校验架构设计

---

## 5. MVP 范围

✅ **做**
- `RequirementSpec` 数据结构
- `load_spec()` — 从 YAML 文件加载
- `validate_task()` — 校验 Task 是否关联有效 Spec
- `validate_change()` — 校验变更是否在范围内
- `validate_feature()` — 校验单个功能是否合规
- `must_have` 检查（必须功能存在）
- `must_not_have` 检查（禁止功能拒绝）
- 未定义功能警告（不阻止）
- pytest 测试覆盖（≥15 个）

❌ **不做**
- RBAC（权限管理）
- Audit（审计日志）
- K8S 集成
- LLM 辅助判断
- Spec Guard
- Architecture Guard
- Scheduler 修改
- Executor 修改

---

## 6. 非目标

| 非目标 | 原因 |
|--------|------|
| RBAC | 权限管理独立演进 |
| Audit | 审计日志独立演进 |
| K8S | 当前 MVP 无 K8s 部署需求 |
| Spec Guard | v0.3.2 之后的下一步 |
| Architecture Guard | 超出本期范围 |
| LLM 辅助 | 先规则驱动，确定性优先 |