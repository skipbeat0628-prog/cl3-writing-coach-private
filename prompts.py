"""Prompt builders for the two intentionally separate coaching modes."""

from __future__ import annotations


def _essay_context(data: dict) -> tuple[str, str, str, str]:
    title = str(data.get("title", "")).strip()
    grade = str(data.get("grade", "")).strip()
    goal = str(data.get("goal", "")).strip()
    content = str(data.get("content", "")).strip()
    if not title or not content:
        raise ValueError("請填寫作文題目與內容")
    if len(content) > 20_000:
        raise ValueError("作文內容過長，最多 20,000 字")
    return title, grade, goal, content


def build_discovery_prompt(data: dict) -> str:
    """Divergent mode: discover possible coaching directions."""
    title, grade, goal, content = _essay_context(data)
    return f"""你是台灣繁體中文的兒童作文批改教練。請分析下方作文，並嚴格依指定 JSON Schema 輸出。

這是「找點模式」：你的任務是發散，提出老師可能想採用的閱讀與批改方向，不替老師做最後判斷。

原則：
- 使用台灣繁體中文與學生能理解的生活白話。
- 先理解作者真正寫出的經驗，不腦補背景、不做人格或心理診斷。
- highlights 選 1 到 3 個確實出現在原文的短引句，指出具體寫作效果。
- life_experience 聚焦一個具體生活細節；coach_response 是老師可以參考的溫暖回應，但不可替作者加大道理。
- suggestions 給 3 個小而可執行、彼此不同的下一步，每項一到兩句。
- typos 只列高度確定的錯別字或標點問題；沒有就回傳空陣列。
- outline 依實際段落整理；每段一項，heading 簡短，summary 說明該段作用。
- boundary_reminder 提醒教練回應時不要過度詮釋之處。
- 不要呼叫工具、不要讀取檔案、不要修改任何內容，只完成文字分析。

年級：{grade or '未提供'}
題目：{title}
教學目標：{goal or '未提供'}
作文原文：
---
{content}
---
"""


def build_enrichment_prompt(data: dict) -> str:
    """Convergent mode: express only the directions selected by the teacher."""
    title, grade, goal, content = _essay_context(data)
    teacher_focus = str(data.get("teacherFocus", "")).strip()
    requested_genre = str(data.get("genre", "自動判斷")).strip() or "自動判斷"
    discovery_genre = str(data.get("discoveryGenre", "")).strip()
    if not teacher_focus:
        raise ValueError("請先輸入想對學生說的重點")
    if len(teacher_focus) > 5_000:
        raise ValueError("老師批改重點過長，最多 5,000 字")

    return f"""你是台灣繁體中文的兒童作文評語編寫助手。請嚴格依指定 JSON Schema 輸出。

這是「評語豐富模式」，不是找點模式。老師已經完成教育判斷；你只能收斂、整理與表達老師選定的意思。

最高優先規則：
1. 老師批改重點是唯一可發展的評語方向。不得新增老師沒提出的缺點、批評、教學目標或修改要求，即使你在作文中發現其他問題也必須忽略。
2. 可以引用原文佐證、把抽象建議變成孩子做得到的動作、補自然銜接、適度加入引導問題與具體鼓勵；不可改變老師立場。
3. 保留老師原本口語、溫度與個人語感，不要洗成制式 AI 文句。豐富是增加理解、行動與被理解感，不是單純拉長。
4. 尊重孩子的聲音、幽默、奇特想法與創作世界；不把文章改造成成人的標準作文，不做人格或心理診斷。
5. 只帶學生走前方一兩步。依年級與文章目前呈現的能力調整難度，不在學生評語裡貼「發展階段」或「寫作動機」標籤。
6. 使用台灣繁體中文，簡單但不幼稚；避免「情感張力、敘事節奏、論證薄弱、意象經營」等抽象術語。

文體使用方式：
- 老師指定的文體優先，只有「自動判斷」時才推測；不明確可用「其他／混合」，不要過度自信。
- 若選擇「自動判斷」且找點模式已有文體，可優先沿用該結果，再依原文確認。
- 記敘文：把方向落到事件、前因後果、人物動作、對話、場景、五感、心情變化與值得放大的片段。
- 抒情文：把抽象情緒連回真實經驗、畫面、意象與個人聲音，不只要求優美詞語。
- 說明文：關注對象、順序、分類、例子、因果與讀者能否理解，不硬塞故事或情緒。
- 議論文：用孩子懂的問題處理主張、理由、例子、不同觀點與結論，不堆抽象術語。
- 故事／創作：從故事內部理解角色欲望、衝突、選擇、轉折、設定與結局，不因不符合現實而否定創意。
- 其他／混合：依主要寫作目的引導，次要文體只作輔助，不替學生貼標籤。

輸出要求：
- final_comment 預設三個自然段落、不顯示段落標題，約 180～450 個中文字：具體欣賞；發展老師指定的 1～2 個方向；自然收束與鼓勵／共情／祝福。
- 老師若沒有要求某一段批評，final_comment 不得自行加入。
- 不要每次套相同開場與結尾；不要空泛說「你好棒、繼續加油」。
- intent_summary 用一句話說明你理解到的老師意圖，供老師核對，不是給學生看的評語。
- preserved_points 列出實際保留並發展的老師重點，不能混入新方向。

老師指定文體：{requested_genre}
找點模式文體（可能空白，僅供自動判斷時參考）：{discovery_genre or '未提供'}
年級：{grade or '未提供'}
題目：{title}
教學目標（僅供理解，不得在老師未要求時硬塞進評語）：{goal or '未提供'}

老師想對學生說的重點：
---
{teacher_focus}
---

學生作文原文：
---
{content}
---

不要呼叫工具、不要讀取檔案、不要修改任何內容，只完成評語整理。
"""
