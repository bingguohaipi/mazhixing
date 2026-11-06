"""批量写入 GESP 入门公共题库（幂等：按标题跳过已存在题目）。"""

from __future__ import annotations

from app.db.session import SessionLocal
from app.knowledge import registry as knowledge_registry
from app.models.problem import Problem, ProblemScope
from app.models.user import User, UserRole
from app.schemas.problem_schema import ProblemCreateRequest, TestCaseInput
from app.services.admin_service import AdminPublicProblemService

knowledge_registry.load_from_defaults()


def _batch() -> list[ProblemCreateRequest]:
    return [
    ProblemCreateRequest(
        title="电影票总价",
        description="已知一位小朋友的电影票价是10元，计算 x 位小朋友的总票价是多少？",
        languages=["C++"],
        difficulty="入门",
        gesp_level="GESP1",
        knowledge_points=["输入输出", "变量与运算"],
        input_format="输入 x。",
        output_format="人数和电影票总价，中间用一个空格隔开。",
        sample_input="2",
        sample_output="2 20",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            TestCaseInput(input_data="2", expected_output="2 20", is_sample=True, sort_order=0),
            TestCaseInput(input_data="5", expected_output="5 50", is_sample=False, sort_order=1),
            TestCaseInput(input_data="1", expected_output="1 10", is_sample=False, sort_order=2),
        ],
    ),
    ProblemCreateRequest(
        title="【例1.4】牛吃牧草",
        description=(
            "有一个牧场，牧场上的牧草每天都在匀速生长，这片牧场可供15头牛吃20天，"
            "或可供20头牛吃10天，那么，这片牧场每天新生的草量可供几头牛吃1天？"
        ),
        languages=["C++"],
        difficulty="入门",
        gesp_level="GESP1",
        knowledge_points=["变量与运算"],
        input_format="（无）",
        output_format="如题述，牛的数量（整数）。",
        sample_input="",
        sample_output="10",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            TestCaseInput(input_data="", expected_output="10", is_sample=True, sort_order=0),
        ],
    ),
    ProblemCreateRequest(
        title="1002: 输出第二个整数",
        description=(
            "输入三个整数，整数之间由一个空格分隔，整数是32位有符号整数。"
            "把第二个输入的整数输出。"
        ),
        languages=["C++"],
        difficulty="入门",
        gesp_level="GESP1",
        knowledge_points=["输入输出"],
        input_format="只有一行，共三个整数，整数之间由一个空格分隔。整数是32位有符号整数。",
        output_format="只有一行，一个整数，即输入的第二个整数。",
        sample_input="123 456 789",
        sample_output="456",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            TestCaseInput(
                input_data="123 456 789",
                expected_output="456",
                is_sample=True,
                sort_order=0,
            ),
            TestCaseInput(input_data="0 -1 2", expected_output="-1", is_sample=False, sort_order=1),
        ],
    ),
    ProblemCreateRequest(
        title="1003: 对齐输出",
        description=(
            "读入三个整数，按每个整数占8个字符的宽度，右对齐输出它们，"
            "按照格式要求依次输出三个整数，之间以一个空格分开。"
        ),
        languages=["C++"],
        difficulty="入门",
        gesp_level="GESP1",
        knowledge_points=["输入输出", "变量与运算"],
        input_format="只有一行，包含三个整数，整数之间以一个空格分开。",
        output_format="只有一行，按照格式要求依次输出三个整数，之间以一个空格分开。",
        sample_input="123456789 0 -1",
        sample_output="123456789        0       -1",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            TestCaseInput(
                input_data="123456789 0 -1",
                expected_output="123456789        0       -1",
                is_sample=True,
                sort_order=0,
            ),
            TestCaseInput(
                input_data="1 2 3",
                expected_output="       1       2       3",
                is_sample=False,
                sort_order=1,
            ),
        ],
    ),
    ProblemCreateRequest(
        title="1004: 字符三角形",
        description="给定一个字符，用它构造一个底边长5个字符、高3个字符的等腰字符三角形。",
        languages=["C++"],
        difficulty="入门",
        gesp_level="GESP1",
        knowledge_points=["输入输出", "循环结构"],
        input_format="输入只有一行，包含一个字符。",
        output_format="一个由该字符构成的、底边长5个字符、高3个字符的等腰三角形。",
        sample_input="*",
        sample_output="  *\n ***\n*****",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            TestCaseInput(input_data="*", expected_output="  *\n ***\n*****", is_sample=True, sort_order=0),
            TestCaseInput(input_data="#", expected_output="  #\n ###\n#####", is_sample=False, sort_order=1),
        ],
    ),
    ProblemCreateRequest(
        title="1005: 地球人口承载力估计",
        description=(
            "假设地球上的新生资源按恒定速度增长。照此测算，地球上现有资源加上新生资源"
            "可供 x 亿人生活 a 年，或供 y 亿人生活 b 年。为了能够实现可持续发展，"
            "避免资源枯竭，地球最多能够养活多少亿人？"
        ),
        languages=["C++"],
        difficulty="简单",
        gesp_level="GESP1",
        knowledge_points=["变量与运算"],
        input_format=(
            "一行，包括四个正整数 x, a, y, b，两个整数之间用单个空格隔开。"
            "x > y, a < b, ax < by，各整数均不大于 10000。"
        ),
        output_format="一个实数 z，表示地球最多养活 z 亿人，舍入到小数点后两位。",
        sample_input="110 90 90 210",
        sample_output="75.00",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            TestCaseInput(
                input_data="110 90 90 210",
                expected_output="75.00",
                is_sample=True,
                sort_order=0,
            ),
            TestCaseInput(
                input_data="12 10 10 15",
                expected_output="6.00",
                is_sample=False,
                sort_order=1,
            ),
        ],
    ),
    ]


def seed_public_gesp_batch() -> None:
    db = SessionLocal()
    try:
        admin = (
            db.query(User)
            .filter(User.role == UserRole.ADMIN, User.deleted_at.is_(None))
            .order_by(User.id.asc())
            .first()
        )
        if admin is None:
            print("skip: no admin user")
            return

        service = AdminPublicProblemService(db)
        created = 0
        skipped = 0
        knowledge_registry.reload_from_db(db)
        for payload in _batch():
            exists = (
                db.query(Problem.id)
                .filter(
                    Problem.scope == ProblemScope.PUBLIC,
                    Problem.title == payload.title,
                    Problem.deleted_at.is_(None),
                )
                .first()
            )
            if exists:
                skipped += 1
                continue
            service.create_problem(admin.id, payload)
            created += 1
            print(f"created: {payload.title}")
        print(f"done: created={created}, skipped={skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_public_gesp_batch()
