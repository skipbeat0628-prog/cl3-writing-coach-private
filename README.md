# CL3 作文批改教練

這是 CL3 極簡版作文批改網頁的私人備份。儲存庫不包含試算表 ID、後台網址或連線密碼。

## 資料夾裡有什麼

- `index.html`：完整網頁，直接用瀏覽器開啟即可使用。
- `google-apps-script/Code.gs`：連接 Google 試算表的後台程式。

## 上傳到 GitHub

1. 在 GitHub 建立新的儲存庫。
2. Visibility 務必選擇 **Private**。
3. 點 `Add file` → `Upload files`。
4. 把這個資料夾內的檔案全部拖進去。
5. 點 `Commit changes` 完成上傳。

## 重要提醒

請勿把試算表 ID 或連線密碼直接寫進程式碼。請在 Apps Script 的「專案設定 → 指令碼屬性」中建立 `SPREADSHEET_ID` 與 `ACCESS_KEY`，開啟網頁後再輸入部署網址和同一組連線密碼。

目前 Google Apps Script 已部署完成。只要後台程式沒有變更，不需要重新部署。

## 使用方式

下載或打開 `index.html`，輸入 Google Apps Script 的 `/exec` 部署網址及連線密碼。按「儲存草稿」或「完成批改」時，資料會寫入指定試算表。
