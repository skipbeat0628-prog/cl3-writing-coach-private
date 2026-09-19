import sys
import json
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prompts import build_discovery_prompt, build_enrichment_prompt, build_cap_prompt


BASE = {
    "title": "雨天",
    "grade": "國小四年級",
    "goal": "寫出事情與感受",
    "content": "爸爸站在門口等我。我跑過去抱住他。",
}


class PromptContractTests(unittest.TestCase):
    def test_discovery_and_enrichment_have_separate_responsibilities(self):
        discovery = build_discovery_prompt(BASE)
        enrichment = build_enrichment_prompt({**BASE, "teacherFocus": "喜歡開頭；爸爸可以多寫"})
        self.assertIn("發散", discovery)
        self.assertIn("article_summary", discovery)
        self.assertIn("只能收斂", enrichment)
        self.assertNotEqual(discovery, enrichment)

    def test_enrichment_requires_teacher_direction(self):
        with self.assertRaisesRegex(ValueError, "想對學生說的重點"):
            build_enrichment_prompt(BASE)

    def test_title_is_optional_when_content_exists(self):
        prompt = build_discovery_prompt({**BASE, "title": ""})
        self.assertIn("題目：未命名作文", prompt)

    def test_teacher_direction_is_highest_priority(self):
        prompt = build_enrichment_prompt({**BASE, "teacherFocus": "只鼓勵結尾"})
        self.assertIn("唯一可發展", prompt)
        self.assertIn("不得新增老師沒提出", prompt)
        self.assertIn("只鼓勵結尾", prompt)

    def test_explicit_genre_is_preserved(self):
        prompt = build_enrichment_prompt({**BASE, "teacherFocus": "理由可以舉例", "genre": "議論文"})
        self.assertIn("老師指定文體：議論文", prompt)
        self.assertIn("主張、理由、例子", prompt)

    def test_found_genre_is_shared_for_auto_mode(self):
        prompt = build_enrichment_prompt({
            **BASE,
            "teacherFocus": "喜歡爸爸出現的地方",
            "genre": "自動判斷",
            "discoveryGenre": "記敘文",
        })
        self.assertIn("找點模式文體", prompt)
        self.assertIn("記敘文", prompt)

    def test_child_friendly_and_creative_world_constraints_exist(self):
        prompt = build_enrichment_prompt({**BASE, "teacherFocus": "角色可以多做一個選擇", "genre": "故事／創作"})
        self.assertIn("只帶學生走前方一兩步", prompt)
        self.assertIn("不因不符合現實而否定創意", prompt)
        self.assertIn("簡單但不幼稚", prompt)

    def test_cap_prompt_uses_official_holistic_rubric(self):
        prompt = build_cap_prompt({**BASE, "grade": "國中二年級"})
        self.assertIn("寫作測驗評分規準", prompt)
        self.assertIn("不要以四面向分數平均", prompt)
        self.assertIn("原文短引句", prompt)
        self.assertIn("手寫格式", prompt)
        self.assertIn("只提出一個優先改善方向", prompt)
        schema = json.loads((Path(__file__).resolve().parents[1] / "cap_schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["dimensions"]["items"]["required"], ["name", "level", "conclusion", "quote", "reason"])
        self.assertIn("priority_title", schema["required"])
        self.assertNotIn("rewritten_example", schema["required"])

    def test_cap_prompt_rejects_primary_grade(self):
        with self.assertRaisesRegex(ValueError, "適用國中作文"):
            build_cap_prompt(BASE)


if __name__ == "__main__":
    unittest.main()
