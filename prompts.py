"""Prompt builders for the two intentionally separate coaching modes."""

from __future__ import annotations

import json


def _essay_context(data: dict) -> tuple[str, str, str, str]:
    title = str(data.get("title", "")).strip()
    grade = str(data.get("grade", "")).strip()
    goal = str(data.get("goal", "")).strip()
    content = str(data.get("content", "")).strip()
    if not content:
        raise ValueError("請填寫作文內容")
    if len(content) > 20_000:
        raise ValueError("作文內容過長，最多 20,000 字")
    return title or "未命名作文", grade, goal, content


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
- article_summary 用 100 字以內概述這篇文章實際寫了什麼，不加入原文沒有的情節或評價。
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
    discovery_analysis = data.get("discoveryAnalysis")
    discovery_context = (
        json.dumps(discovery_analysis, ensure_ascii=False, separators=(",", ":"))
        if isinstance(discovery_analysis, dict)
        else "未提供"
    )
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
7. 找點模式結構化結果是這篇作文已完成的分析，只能作為佐證與上下文；不要重新執行找點、不要另列亮點、錯字、大綱或新建議。最終評語仍只沿用老師選入「老師想對學生說的重點」的內容。

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

已保存的找點模式結構化結果（可能未提供）：
---
{discovery_context}
---

學生作文原文：
---
{content}
---

不要呼叫工具、不要讀取檔案、不要修改任何內容，只完成評語整理。
"""


def build_cap_prompt(data: dict) -> str:
    """Evidence-led advisory assessment for Taiwan's CAP Chinese writing test."""
    title, grade, goal, content = _essay_context(data)
    if grade and not any(token in grade for token in ("國中", "七年級", "八年級", "九年級", "國一", "國二", "國三")):
        raise ValueError("會考模式適用國中作文，請先將年級改為國中")
    return f"""你是熟悉國中教育會考寫作測驗規準的台灣國文教師。請依指定 JSON Schema 輸出，提供老師複核用的參考評估，不宣稱正式閱卷結果。

評分依據：國中教育會考官方「寫作測驗評分規準」（https://cap.rcpet.edu.tw/exam3-1.html）。整篇文章給 1–6 級分；完全離題、只訂題目、僅抄題目或題幹、詩歌體、空白卷才考慮 0 級分。不要以四面向分數平均、四捨五入來產生總級分。題目若未提供完整題幹或材料，勿臆測任務要求，並在 limitations 說明。

評估流程必須依序進行：先讀全文、理解題目要求（若只有題名，承認資訊不足）、主旨、主要內容與段落；再逐軸檢視立意取材、結構組織、遣詞造句、錯別字／格式／標點；四軸完成後才判斷整體級分；最後選出唯一最值得優先改善的一點。不要一開始憑印象猜總級分。

各面向給 level 1–6，並分別輸出 conclusion（一句結論）、quote（原文短引句）、reason（證據如何支持判斷的簡短理由）。引用必須逐字出現在學生原文；沒有可引用的內容時 quote 用空字串並在 reason 說明。格式面向只根據貼入的文字判斷錯字與標點，不假裝看過手寫卷面。四面向只作診斷，最終整體級分需依全文與官方級距綜合判斷；分界不明時保持審慎，在 limitations 說明。級距錨點如下：
- 6：切題且能統整、深化材料凸顯主旨；結構完整連貫；用詞精確、句型有效；幾乎無錯。
- 5：能統整材料並闡述主旨；結構完整，偶有轉折不順；用詞正確、句型通順；少量錯誤不影響文意。
- 4：尚能統整材料並說明主旨；結構大致完整，偶有不連貫；表意大致清楚，偶有贅詞或句型單一；一些錯誤但理解無大礙。
- 3：材料發展不充分；結構鬆散或不連貫；用詞錯誤或贅詞較多；錯字標點可能妨礙理解。
- 2：材料運用不足或大量引述題幹、發展有限；結構不完整；語句常有錯誤；錯字標點多。
- 1：僅解題或材料極簡；無明顯結構；語句難理解；格式標點錯誤極多。

dimension 順序固定為「立意取材」「結構組織」「遣詞造句」「錯別字、格式與標點符號」。先完成四面向證據，再給 overall_level 與 overall_reason；overall_reason 用 2–4 句說明整體表現及為何落在這一級，不能只憑單一錯誤。只提出一個優先改善方向：priority_title 是短標題，priority_detail 必須指出原文具體位置、下一步可做的動作，並給一個保留原意與學生自然聲音的示例句；不要額外列出其他修改清單。用國中生能懂的繁體中文、中性尊重語氣，不羞辱或做人格價值判斷。不猜測或依姓名、性別、家庭、族群、母語背景評分。不因用詞樸實或可能的背景印象降低級分。純文字無法判斷手寫格式與卷面，應在 limitations 明說。

年級：{grade or '國中（未細分）'}
題目：{title}
教學目標（僅供參考，不代替會考規準）：{goal or '未提供'}
學生作文原文：
---
{content}
---

不要呼叫工具、讀取檔案或修改內容。
"""
