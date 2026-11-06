"""Standard knowledge-point catalog for student practice and problem tagging."""

from __future__ import annotations

from dataclasses import dataclass
@dataclass(frozen=True)
class KnowledgePointEntry:
    name: str
    summary: str
    content_markdown: str
    sort_order: int = 100


def _md(name: str, what: str, how: str, example: str = "", tip: str = "") -> str:
    example_block = example.strip() or "可以从本题库中该知识点下的入门题开始练手，边做边对照思路。"
    parts = [
        "## 描述",
        what,
        "",
        "## 怎么学 / 怎么用",
        how,
        "",
        "## 小例子",
        example_block,
    ]
    if tip:
        parts.extend(["", "## 小贴士", tip])
    return "\n".join(parts)


# fmt: off
_ENTRIES: list[KnowledgePointEntry] = [
    KnowledgePointEntry(
        "输入输出",
        "读入数据、按格式输出结果（含无输入的 Hello World 等入门题），信奥第一步。",
        _md(
            "输入输出",
            "输入输出指程序从标准输入读取数据，并向标准输出打印结果。OJ 判题时，你的代码读入的就是测试用例里的输入文本。"
            "不少入门题只要求输出字符串或数字，无需读入。",
            "先看清题目要求的输入格式（几个数、是否多行），再写 `cin`/`scanf` 或 Python 的 `input()`；"
            "输出时注意空格、换行与小数位数；无输入题可留空输入，只写 `print`/`cout` 即可。",
            "```cpp\nint a, b;\ncin >> a >> b;\ncout << a + b;\n```\n\n```python\na, b = map(int, input().split())\nprint(a + b)\n```\n\n```cpp\ncout << \"Hello World\";\n```",
            "无输入的题（如 Hello World）可以留空输入，只写输出即可。",
        ),
        1,
    ),
    KnowledgePointEntry("变量与运算", "定义变量、赋值与加减乘除、取余等基本运算。", _md(
        "变量与运算",
        "变量像带标签的盒子，存放数字或字符；运算规则与数学类似，整除和取余在编程里很常用。",
        "先确定数据类型（整型/浮点），注意整数除法和类型转换，避免溢出。",
        "```python\nr = 2\narea = 3.14 * r * r\nprint(f\"{area:.2f}\")\n```",
    ), 3),
    KnowledgePointEntry("条件语句", "用 if / else 根据条件走不同分支。", _md(
        "条件语句",
        "条件语句让程序「会判断」：条件成立执行 A，否则执行 B。",
        "把题目条件翻译成布尔表达式；注意边界（等于、大于、能否整除）。",
        "```cpp\nif (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0))\n  cout << \"YES\";\nelse cout << \"NO\";\n```",
    ), 4),
    KnowledgePointEntry("循环结构", "for / while 重复执行，处理重复计算与遍历。", _md(
        "循环结构",
        "循环用于重复做同一件事：例如打印九九表、累加 1 到 n、遍历每一位数字。",
        "先想循环次数或结束条件；内层循环注意变量不要写错；多层循环想清每一层含义。",
        "```cpp\nfor (int i = 1; i <= 9; i++) {\n  for (int j = 1; j <= i; j++)\n    cout << j << \"*\" << i << \"=\" << i*j << \"\\t\";\n  cout << \"\\n\";\n}\n```",
        "死循环是常见错误，确保循环变量会朝结束条件变化。",
    ), 5),
    KnowledgePointEntry("数组", "同类型元素连续存放，用下标 O(1) 访问。", _md(
        "数组",
        "数组把多个同类型数据排成一行，用 0 开始的下标访问。内存里通常连续存储，所以按下标读取很快。",
        "定义长度足够的数组；遍历常用 for；注意下标不要越界。二维数组可表示矩阵或表格。",
        "```python\nnums = [10, 20, 30]\nprint(nums[0], nums[-1])\nfor x in nums:\n    print(x)\n```\n\n```\n下标:  0    1    2\n值:   10   20   30\n```",
    ), 10),
    KnowledgePointEntry("字符串", "字符序列，常用遍历、拼接、比较与子串。", _md(
        "字符串",
        "字符串是一串字符，如姓名、单词。题目常考查找、反转、统计、匹配。",
        "C++ 用 `string`，Python 用 `str`；注意下标、切片；比较大小写是否敏感。",
        "```python\ns = \"hello\"\nprint(s[::-1])  # olleh\n```",
    ), 11),
    KnowledgePointEntry("哈希表", "键到值的映射，平均 O(1) 查找与计数。", _md(
        "哈希表",
        "哈希表（字典）适合「出现过吗」「出现几次」「某值对应什么」这类问题。",
        "Python 用 `dict` 或 `Counter`；C++ 用 `unordered_map`。键一般是数字或字符串。",
        "```python\nfrom collections import Counter\ncnt = Counter(\"abca\")\nprint(cnt[\"a\"])  # 2\n```",
    ), 12),
    KnowledgePointEntry("数学", "数论、公式、 gcd、快速幂等数学工具。", _md(
        "数学",
        "很多题本质是数学：整除、余数、质数、最大公约数、组合计数等。",
        "先化简公式再写代码；注意数据范围，必要时用 long long 或取模。",
        "```python\nimport math\nprint(math.gcd(12, 18))  # 6\n```",
    ), 13),
    KnowledgePointEntry("动态规划", "把大问题拆成重叠子问题，记忆化最优解。", _md(
        "动态规划",
        "动态规划（DP）适用于「最优子结构 + 重叠子问题」，如最长上升子序列、背包、路径计数。",
        "1. 定义状态 `dp[i]` 含义；2. 写转移方程；3. 确定初始值与遍历顺序。",
        "```python\n# 斐波那契\ndp = [0, 1, 1]\nfor i in range(3, 10):\n    dp.append(dp[-1] + dp[-2])\n```",
        "先从暴力递归 + 记忆化入手，再改迭代。",
    ), 14),
    KnowledgePointEntry("排序", "将元素按大小 rearrange，便于查找与贪心。", _md(
        "排序",
        "排序是最常用的预处理：升序后双指针、二分、相邻比较都更简单。",
        "小数据可用冒泡/选择；一般直接用语言内置 `sort`；注意是否稳定、是否降序。",
        "```python\na = [3, 1, 2]\na.sort()\nprint(a)\n```",
    ), 15),
    KnowledgePointEntry("贪心", "每步做当前看起来最优的选择。", _md(
        "贪心",
        "贪心在局部最优能推出全局最优时非常高效，如活动选择、部分背包、区间调度。",
        "先证明或直觉上判断贪心正确；常见套路是按结束时间、按差值排序。",
        "反例：硬币 1,3,4 凑 6，贪心 4+1+1 不是最少枚数。",
    ), 16),
    KnowledgePointEntry("深度优先搜索", "DFS：一条路走到底再回溯。", _md(
        "深度优先搜索",
        "DFS 用递归或栈实现，适合遍历树/图、全排列、连通块、迷宫。",
        "写清「进入节点 / 离开节点」；记得 visited 防重复；回溯时撤销选择。",
        "```python\ndef dfs(u):\n    visited.add(u)\n    for v in graph[u]:\n        if v not in visited:\n            dfs(v)\n```",
    ), 17),
    KnowledgePointEntry("广度优先搜索", "BFS：按层扩展，求最短步数。", _md(
        "广度优先搜索",
        "BFS 用队列，适合无权图最短路、层次遍历、最少操作次数。",
        "入队时标记距离；同一层一起处理；注意队列空则结束。",
        "```python\nfrom collections import deque\nq = deque([start])\n```",
    ), 18),
    KnowledgePointEntry("二分查找", "在有序序列上 O(log n) 定位。", _md(
        "二分查找",
        "二分要求单调性：答案越大越可行（或越小越可行）。每次砍掉一半搜索空间。",
        "写 `while lo < hi`， mid 计算防溢出；区分找第一个/最后一个满足的位置。",
        "```python\nlo, hi = 0, len(a) - 1\nwhile lo <= hi:\n    mid = (lo + hi) // 2\n```",
    ), 19),
    KnowledgePointEntry("位运算", "按二进制位与、或、异或、移位操作。", _md(
        "位运算",
        "位运算用于状态压缩、奇偶、子集枚举、判断 2 的幂等。",
        "`& | ^ ~ << >>`；常用 `x & 1` 看最低位；`1 << k` 表示第 k 位为 1。",
        "```python\nprint(5 & 1)   # 1 奇数\nprint(1 << 3)  # 8\n```",
    ), 20),
    KnowledgePointEntry("树", "节点与边组成的无环连通结构。", _md(
        "树",
        "树是 n 个节点 n-1 条边的连通图，有根树、子树、深度、高度等概念。",
        "递归处理子树；DFS/BFS 遍历；注意父子关系与回溯。",
    ), 21),
    KnowledgePointEntry("二叉树", "每个节点最多两个孩子。", _md(
        "二叉树",
        "二叉树常考遍历（前中后序、层序）、高度、对称、路径和。",
        "递归模板：处理根 → 递归左 → 递归右；空节点返回边界值。",
    ), 22),
    KnowledgePointEntry("链表", "节点通过指针/next 串成链。", _md(
        "链表",
        "链表插入删除 O(1) 但查找 O(n)。常考反转、环检测、合并有序链。",
        "使用 dummy 头结点简化插入；快慢指针找中点或环。",
    ), 23),
    KnowledgePointEntry("栈", "后进先出 LIFO，模拟与单调栈。", _md(
        "栈",
        "栈像一摞盘子：最后放进去的先拿出来。适合括号匹配、表达式求值、单调栈求下一个更大。",
        "语言自带 `stack` 或列表 `append/pop`；注意空栈判断。",
    ), 24),
    KnowledgePointEntry("队列", "先进先出 FIFO，配合 BFS。", _md(
        "队列",
        "队列像排队：先来的先服务。BFS、滑动窗口有时用双端队列。",
        "Python `collections.deque` 两端 O(1) 入队出队。",
    ), 25),
    KnowledgePointEntry("堆（优先队列）", "随时取最大/最小元素。", _md(
        "堆（优先队列）",
        "堆维护动态最值：TopK、合并 K 路有序、Dijkstra 优化。",
        "Python `heapq` 是小根堆；存负数模拟大根堆。",
        "```python\nimport heapq\nh = []\nheapq.heappush(h, 3)\n```",
    ), 26),
    KnowledgePointEntry("矩阵", "二维数组表示网格或表格。", _md(
        "矩阵",
        "矩阵题考遍历、旋转、前缀和、模拟移动、连通块。",
        "注意行列下标 `(i,j)` 与边界；方向数组 dx,dy 四联通/八联通。",
    ), 27),
    KnowledgePointEntry("双指针", "两个下标协同扫描有序或数组。", _md(
        "双指针",
        "对撞指针、快慢指针、同向滑动：在 O(n) 内完成配对或去重。",
        "有序数组找两数和：一头一尾向中间夹。",
    ), 28),
    KnowledgePointEntry("滑动窗口", "维护区间 [l,r] 的连续子数组性质。", _md(
        "滑动窗口",
        "固定或可变长度窗口，在 O(n) 内统计满足条件的子串/子数组。",
        "右扩左缩：不满足时移动左边界；记录窗口内计数用哈希表。",
    ), 29),
    KnowledgePointEntry("前缀和", "预处理区间和，O(1) 查询任意区间。", _md(
        "前缀和",
        "`pre[i]` 表示前 i 个元素之和，区间 [l,r] 和 = `pre[r+1]-pre[l]`。",
        "二维前缀和可求子矩阵和；差分数组是前缀和的逆操作。",
    ), 30),
    KnowledgePointEntry("回溯", "尝试 + 撤销，枚举所有可能解。", _md(
        "回溯",
        "排列组合、子集、N 皇后、数独：选或不选，递归后恢复现场。",
        "模板：for 选择 in 可选列表 → 做选择 → 递归 → 撤销选择。",
    ), 31),
    KnowledgePointEntry("分治", "拆成子问题，合并结果。", _md(
        "分治",
        "归并排序、快速排序、最近点对：分 → 解 → 合。",
        "注意子问题规模减半后的合并代价。",
    ), 32),
    KnowledgePointEntry("递归", "函数调用自身，表达重复结构。", _md(
        "递归",
        "树、分治、DFS 都依赖递归。必须有终止条件，避免无限调用。",
        "写清「当前层做什么」和「交给下一层什么更小的问题」。",
    ), 33),
    KnowledgePointEntry("模拟", "按题意直接一步步模拟过程。", _md(
        "模拟",
        "实现题面规则：方向移动、时钟、字符串操作。关键是细节不丢。",
        "用变量表示状态；复杂时分函数；注意 long long。",
    ), 34),
    KnowledgePointEntry("枚举", "遍历所有可能答案并检验。", _md(
        "枚举",
        "数据范围小时直接枚举：暴力、全排列、双重循环配对。",
        "剪枝：不满足条件提前 continue；先估算范围能否通过时限。",
    ), 35),
    KnowledgePointEntry("并查集", "维护集合合并与是否同一组。", _md(
        "并查集",
        "连通性、 Kruskal 最小生成树：路径压缩 + 按秩合并。",
        "`find(x)` 找根；`union(a,b)` 合并。",
    ), 36),
    KnowledgePointEntry("拓扑排序", "有向无环图上的线性次序。", _md(
        "拓扑排序",
        "课程表、任务依赖：入度为 0 的先做，BFS 或 DFS 后序。",
        "若排序数量不足 n，说明有环。",
    ), 37),
    KnowledgePointEntry("字典树", "Trie：按字符前缀组织的树。", _md(
        "字典树",
        "多字符串前缀查询、自动补全：每个节点是字符，边表示下一个字符。",
        "节省前缀重复存储；注意节点数组大小 26 或动态。",
    ), 38),
    KnowledgePointEntry("线段树", "区间修改与区间查询的对数数据结构。", _md(
        "线段树",
        "区间最值、区间和、懒标记区间加：适合 n 大、操作多。",
        "信奥进阶内容，先掌握暴力与前缀和再学。",
    ), 39),
    KnowledgePointEntry("单调栈", "栈内元素保持单调，求下一个更大/更小。", _md(
        "单调栈",
        "典型：柱状图最大矩形、每日温度、接雨水的一部分思路。",
        "入栈前弹出不符合单调性的元素并更新答案。",
    ), 40),
    KnowledgePointEntry("双端队列", "两端可入可出的队列。", _md(
        "双端队列",
        "滑动窗口最值、0-1 BFS 有时需要 deque 头尾插入。",
        "Python `deque` 的 `appendleft`, `popleft`。",
    ), 41),
    KnowledgePointEntry("设计", "实现数据结构或类，满足 API 约束。", _md(
        "设计",
        "LeetCode 式「设计 LRU、栈、队列」：用数组+哈希或链表组合。",
        "先实现功能正确，再优化复杂度。",
    ), 42),
    KnowledgePointEntry("数据库", "SQL 查询与表关系（平台拓展题）。", _md(
        "数据库",
        "SELECT/WHERE/JOIN/GROUP BY 等 SQL 语法与简单查询。",
        "先写清要查哪张表、过滤条件与排序。",
    ), 43),
    KnowledgePointEntry("多线程", "并发与同步（拓展，少儿阶段了解即可）。", _md(
        "多线程",
        "了解线程、锁、并发安全的基本概念即可，信奥主战场仍是算法与数据结构。",
        "做题时关注题面要求的同步模型。",
    ), 44),
    KnowledgePointEntry("脑筋急转弯", "需要特殊观察或结论的趣味题。", _md(
        "脑筋急转弯",
        "不要硬套模板，先找规律、特例、数学结论。",
        "与同学讨论思路往往比闷头写代码更快。",
    ), 45),
    KnowledgePointEntry("概率与统计", "期望、概率与随机过程基础。", _md(
        "概率与统计",
        "古典概型、期望线性性、简单 DP 概率。",
        "注意模数与分数比较方式。",
    ), 46),
    KnowledgePointEntry("未分类", "尚未标注知识点的题目。", _md(
        "未分类",
        "这些题还未归入标准知识点，仍可练习；教师可在编辑题目时选择合适标签。",
        "建议从输入输出、循环、数组等基础标签中选最接近的一项。",
    ), 999),
]
# fmt: on


def default_seed_entries() -> tuple[KnowledgePointEntry, ...]:
    return tuple(_ENTRIES)


def sorted_entries() -> tuple[KnowledgePointEntry, ...]:
    from app.knowledge.registry import sorted_entries as _sorted

    return _sorted()


def catalog_names() -> frozenset[str]:
    from app.knowledge.registry import catalog_names as _names

    return _names()


def get_entry(name: str) -> KnowledgePointEntry | None:
    from app.knowledge.registry import get_entry as _get

    return _get(name)


def validate_knowledge_point_name(name: str | None) -> str:
    key = (name or "").strip()
    if not key:
        raise ValueError("请选择知识点")
    if key not in catalog_names():
        raise ValueError(f"知识点「{key}」不在系统知识点库中，请从下拉列表选择")
    return key


def list_option_items() -> list[dict[str, str]]:
    return [{"name": e.name, "summary": e.summary} for e in sorted_entries() if e.name != "未分类"]
