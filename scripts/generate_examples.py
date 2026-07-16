"""Generate the deterministic fictional demonstration and starter template."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    from textsignal.examples import demo_dataframe, starter_template
    from textsignal.io import dataframe_to_xlsx

    examples = ROOT / "examples"
    examples.mkdir(parents=True, exist_ok=True)
    demo = demo_dataframe()
    template = starter_template()
    demo.to_csv(examples / "textsignal-fictional-corpus.csv", index=False)
    (examples / "textsignal-fictional-corpus.xlsx").write_bytes(
        dataframe_to_xlsx(demo, "Fictional corpus")
    )
    (examples / "textsignal-starter-template.xlsx").write_bytes(dataframe_to_xlsx(template, "Text data"))
    assert len(demo) == 540
    assert demo["response_id"].is_unique
    assert not demo["open_response"].duplicated().any()
    assert demo["user_stage"].nunique() == 2
    assert demo["message_variant"].nunique() == 3
    assert int(demo["message_variant"].value_counts().min()) >= 20


if __name__ == "__main__":
    main()
