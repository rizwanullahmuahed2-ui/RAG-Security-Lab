"""Exercise actual Streamlit widget interactions without launching a browser."""
from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_dashboard_asks_question_and_retains_evidence():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.text_area[0].value
    assert app.session_state["answer"]["result"].retrieved_documents
    assert "exact" == app.session_state["resources"][-1].__class__.__name__.replace("VectorStore", "").lower()
    app.run()
    assert not app.exception and app.text_area[0].value


def test_changed_budget_hides_previous_answer_and_explains_seed():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    app.button[0].click().run()
    assert app.text_area
    app.slider(key="poison_budget").set_value(20).run()
    assert not app.exception
    assert not app.text_area
    assert any("previous answer is hidden" in item.value for item in app.info)
    app.button[0].click().run()
    assert not app.exception and app.text_area
    assert app.session_state["answer"]["selection_key"][2] == 20
    app.number_input(key="selection_seed").set_value(17).run()
    assert not app.text_area


def test_level_comparison_uses_fixed_seeds_and_requested_budgets(monkeypatch, tmp_path):
    calls = []
    def execute(config, experiment, seeds, split, progress):
        calls.append((config.poisoning.counts, experiment, seeds, split))
        return tmp_path, None
    monkeypatch.setattr("src.evaluation.runner.execute", execute)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    app.button(key="compare_levels").click().run()
    assert not app.exception and not app.error
    assert calls == [([0, 10, 20, 50], "poisoning", [42], "all")]


def test_repeated_mode_is_connected_to_question_runner():
    from src.evaluation.question_comparison import REPEATED
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    app.radio(key="attack_mode").set_value(REPEATED).run()
    app.slider(key="poison_budget").set_value(20).run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    saved = app.session_state["answer"]
    assert saved["mode"] == REPEATED
    assert saved["target_copies_injected"] == 20
    assert len(saved["poison_ids"]) == 20
