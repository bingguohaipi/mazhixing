from app.services.ai_analysis_format import pack_ai_analysis, parse_model_json, unpack_ai_analysis


def test_pack_and_unpack_roundtrip() -> None:
    raw = pack_ai_analysis("## 分析\n第 3 行有问题", [3, 3, 5])
    text, lines = unpack_ai_analysis(raw)
    assert "分析" in text
    assert lines == [3, 5]


def test_parse_model_json() -> None:
    payload = '{"highlight_lines":[2,4],"analysis":"第 2 行逻辑错误"}'
    text, lines = parse_model_json(payload)
    assert lines == [2, 4]
    assert "第 2 行" in text


def test_unpack_legacy_plain_text() -> None:
    text, lines = unpack_ai_analysis("第 8 行数组越界")
    assert "第 8 行" in text
    assert 8 in lines
