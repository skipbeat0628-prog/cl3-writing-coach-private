import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prompts import build_discovery_prompt, build_enrichment_prompt


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
        self.assertIn("只能收斂", enrichment)
        self.assertNotEqual(discovery, enrichment)

    def test_enrichment_requires_teacher_direction(self):
        with self.assertRaisesRegex(ValueError, "想對學生說的重點"):
            build_enrichment_prompt(BASE)

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


if __name__ == "__main__":
    unittest.main()
