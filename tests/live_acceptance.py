"""Optional live acceptance checks. Each case consumes Codex usage."""

from __future__ import annotations

import json
import urllib.request


URL = "http://127.0.0.1:8765/api/enrich"


def enrich(name: str, **payload) -> dict:
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=260) as response:
        result = json.loads(response.read().decode("utf-8"))
    output = result["enrichment"]
    print(f"{name}: OK | {output['effective_genre']} | {len(output['final_comment'])} 字")
    print(output["final_comment"].replace("\n", " ")[:180])
    return output


def main() -> None:
    base = {
        "title": "放學的雨",
        "grade": "國小三年級",
        "goal": "把事情寫清楚",
        "content": "放學時下大雨，爸爸站在校門口等我。他的褲管都濕了。我跑過去，他把雨傘往我這邊移，我們一起慢慢走回家。",
    }

    # A + E + F: no discovery result, fragmentary focus, younger student.
    a = enrich(
        "Case A/E/F",
        **base,
        genre="自動判斷",
        discoveryGenre="",
        teacherFocus="喜歡第二段、爸爸那邊可以多寫、結尾鼓勵",
    )
    banned = ["情感張力", "敘事節奏", "意象經營", "文本結構"]
    assert not any(word in a["final_comment"] for word in banned)

    # B: a direction selected in discovery is supplied as teacher intent.
    enrich(
        "Case B",
        **base,
        genre="自動判斷",
        discoveryGenre="記敘文",
        teacherFocus="我想肯定「他把雨傘往我這邊移」這個小動作很溫暖\n可以引導孩子補寫爸爸當時的表情",
    )

    # C: identical direction, different explicit genre and source text.
    c1 = enrich(
        "Case C-記敘文",
        **base,
        genre="記敘文",
        discoveryGenre="",
        teacherFocus="理由可以再說清楚，給孩子一個具體問題",
    )
    c2 = enrich(
        "Case C-議論文",
        title="手機能不能帶到學校",
        grade="國小六年級",
        goal="提出主張和理由",
        content="我覺得學生可以帶手機到學校。因為有事情可以找爸媽，所以我贊成。",
        genre="議論文",
        discoveryGenre="",
        teacherFocus="理由可以再說清楚，給孩子一個具體問題",
    )
    assert c1["effective_genre"] != c2["effective_genre"]
    assert c1["final_comment"] != c2["final_comment"]

    # D: an obvious repetition exists, but the teacher only asks to affirm the ending.
    d = enrich(
        "Case D",
        title="我的早上",
        grade="國小四年級",
        goal="記錄生活",
        content="我我我早上起床，吃了早餐。後來去上學。最後我很開心今天沒有遲到。",
        genre="記敘文",
        discoveryGenre="",
        teacherFocus="只肯定最後沒有遲到的心情，給一句溫暖鼓勵；不要提出修改建議",
    )
    assert not any(word in d["final_comment"] for word in ["重複", "錯字", "我我我"])

    # G: fantasy logic must be respected rather than corrected for realism.
    g = enrich(
        "Case G",
        title="月亮郵差",
        grade="國小五年級",
        goal="創作有轉折的故事",
        content="我騎著會說話的掃把飛到月亮送信。月亮突然打了一個噴嚏，把所有星星吹走了。我決定追上星星，請牠們回家。",
        genre="故事／創作",
        discoveryGenre="",
        teacherFocus="這個世界很有趣；想引導他把追星星時遇到的困難寫清楚；結尾鼓勵",
    )
    assert not any(word in g["final_comment"] for word in ["不合理", "不現實", "不可能"])
    print("Live acceptance checks completed.")


if __name__ == "__main__":
    main()
