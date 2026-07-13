from tokenish_engine.compile import wants_instruction_following
from tokenish_engine.compress.dedupe import dedupe_document_sections
from tokenish_engine.meters.tokens import count_tokens
from tokenish_engine.pipeline import optimize


def test_assess_is_not_follow_mode():
    assert wants_instruction_following("Assess the attached doc.", True) is False
    assert wants_instruction_following("Analyze this PDF", True) is False


def test_follow_instructions_is_follow_mode():
    assert wants_instruction_following(
        "Deeply follow the instructions in the attached document", True
    ) is True


def test_dedupe_drops_page_break_clones():
    block = "Grounded Visual Exhaustion Benchmark prompt body with unique marker ZZZ-42.\n" * 20
    doc = f"{block}\n--- PAGE BREAK ---\n{block}\n--- PAGE BREAK ---\n{block}"
    out, dropped, stage = dedupe_document_sections(doc)
    assert dropped >= 2
    assert "dedupe_drop_" in stage
    assert count_tokens(out) < count_tokens(doc)
    assert "ZZZ-42" in out


def test_assess_duplicate_doc_saves_tokens():
    block = (
        "Grounded Visual Exhaustion Benchmark v1.0. "
        "Analyze Bosch Waldo Raphael exhaustively. Never guess. "
    ) * 40
    doc = "\n--- PAGE BREAK ---\n".join([block, block, block, block])
    result = optimize(
        prompt="Assess the attached doc.",
        files=[("gveb.txt", doc.encode("utf-8"))],
        target_engine="gemini-3.5-flash",
        model="gemini-3.5-flash",
        enable_pxpipe=False,
    )
    assert result.tokex.saved_tokex > 100
    assert result.tokex.saved_pct > 5
    assert any(s.startswith("dedupe_drop_") for s in result.stages)
