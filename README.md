# 心理测试生成器

一个基于Flask的简单心理测试结果生成器。

## GitHub Pages（静态版）访问方式

本仓库包含一个可直接发布到 GitHub Pages 的静态版本，发布目录为 `docs/`。

### 发布步骤（推荐：从 `/docs` 发布）
- 进入 GitHub 仓库页面 → **Settings** → **Pages**
- **Source** 选择 **Deploy from a branch**
- **Branch** 选择 `main`（或你的默认分支）
- **Folder** 选择 **`/docs`**
- 保存后等待 1–5 分钟，在 Pages 页面会显示你的站点链接

### 访问链接规则
- 如果仓库名是 `test`，账号是 `25coffee`，则链接通常是：`https://25coffee.github.io/test/`
- 如果仓库名不同，把链接中的 `test` 替换成你的仓库名即可

> 注意：点击仓库首页看到 README 是正常的；网站入口是 `docs/index.html`，需要用 **GitHub Pages 的 URL** 打开。

## 功能特点

- 输入心理测试名称和选项字母串
- 自动统计哪个选项出现最多
- 根据最多选项显示对应的测试结果
- 测试结果保存在JSON文件中，易于修改

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python app.py
```

3. 在浏览器中访问：
```
http://localhost:5000
```

## 使用方法

1. 在测试编号输入框中输入测试编号（随机乱码，例如：a7K9mP2xQ5vR8nT）
2. 在选项输入框中输入选项字母串（例如：AAABBC）
3. 点击"确认生成"按钮
4. 系统会根据测试编号查找测试，统计哪个选项最多，并显示对应的测试结果和测试名称

## 测试结果文件结构

所有测试保存在统一的 `tests/tests.json` 文件中，文件格式为JSON数组。

JSON文件格式如下：

```json
[
  {
    "test_id": "729f31",
    "test_name": "性格测试",
    "results": {
      "A": "你的测试结果A",
      "B": "你的测试结果B",
      "C": "你的测试结果C",
      "D": "你的测试结果D",
      "E": "你的测试结果E"
    }
  },
  {
    "test_id": "d5abf2",
    "test_name": "另一个测试",
    "results": {
      "A": "结果A",
      "B": "结果B"
    }
  }
]
```

### 字段说明：
- `test_id`: 测试编号（test_name的MD5加密值的前6位，用于唯一标识测试）
- `test_name`: 测试名称（字符串，显示给用户的测试名称）
- `results`: 对象，包含各个选项（A、B、C、D、E等）对应的测试结果

**注意**：`test_id` 必须与 `test_name` 的MD5值前6位一致。例如"性格测试"的MD5前6位是"729f31"。

## 添加新测试

1. 编辑 `tests/tests.json`（或 GitHub Pages 版本的 `docs/tests/tests.json`）
2. 按照已有结构添加/更新测试数据（`test_id`、`test_name`、`results`）

如果测试名称已存在（test_id相同），则会更新该测试；如果不存在，则会添加为新项。

## 文件说明

- `app.py` - Flask应用主文件
- `templates/index.html` - 前端页面模板
- `tests/` - 存放各个测试的JSON配置文件目录
- `requirements.txt` - Python依赖包列表

