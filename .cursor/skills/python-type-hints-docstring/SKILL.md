---
name: python-type-hints-docstring
description: Enforce Python type hints and Google-style docstrings for all Python code. Use when writing new Python functions, methods, classes, or modifying existing Python code that lacks type annotations or documentation.
disable-model-invocation: true
---

# Python Type Hints & Docstrings

## Instructions

Whenever writing Python code (new functions, methods, classes, or modifying existing code), always follow these rules:

### 1. Type Hints

- 所有函数参数和返回值必须加 **type hints**
- 使用 Python 标准 `typing` 模块（兼容 Python 3.7+ 语法）
- 对于容器类型，尽量标注内部元素类型（如 `List[int]`, `Dict[str, Any]`）
- 对于可能为空的变量，使用 `Optional[T]` 或 `Union[T, None]`

### 2. Google Style Docstrings

每个 public 函数/方法/类必须包含 Google 风格的 docstring：

```
Args:
    param_name (type): Description.
    ...

Returns:
    type: Description.

Raises:
    ExceptionType: When/why this exception is raised.
```

### 3. Class Docstrings

public 类要有 docstring，简要描述类的职责和用法。

### 4. Private vs Public

- private 函数（以 `_` 开头）：可以省略 docstring，但 **必须保留 type hints**。
- private 函数如果内部逻辑复杂，也应加 docstring。

## Examples

### Function with type hints and docstring

```python
from typing import Optional, List

def calculate_average(values: List[float], decimals: Optional[int] = None) -> str:
    """计算数值列表的平均值并格式化为字符串。

    Args:
        values: 要计算平均值的浮点数列表。
        decimals: 小数位数，为 None 则保留原始精度。

    Returns:
        格式化后的平均值字符串。

    Raises:
        ValueError: 当 values 为空列表时。
    """
    if not values:
        raise ValueError("values cannot be empty")
    avg = sum(values) / len(values)
    if decimals is not None:
        return f"{avg:.{decimals}f}"
    return str(avg)
```

### Class with type hints and docstring

```python
from typing import Optional

class UserProfile:
    """用户档案，管理用户基本信息和偏好设置。"""

    def __init__(self, user_id: str, display_name: str, email: Optional[str] = None) -> None:
        self.user_id = user_id
        self.display_name = display_name
        self.email = email

    def get_display_info(self) -> str:
        """获取用户显示信息。

        Returns:
            包含用户名和邮箱的摘要字符串。
        """
        email_part = f" <{self.email}>" if self.email else ""
        return f"{self.display_name}{email_part}"
```

### Private function (type hints required, docstring optional)

```python
from typing import List

def _normalize_values(raw: List[float]) -> List[float]:
    # docstring optional for private functions
    total = sum(raw)
    return [v / total for v in raw] if total else raw
```