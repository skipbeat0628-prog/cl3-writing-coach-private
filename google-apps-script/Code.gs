// 作文批改網頁 × Google 試算表
// 這份代碼只要完整貼到 Google Apps Script，不需要逐行修改。

const SHEET_NAME = '工作表1';

// 請在 Apps Script「專案設定 → 指令碼屬性」加入：
// SPREADSHEET_ID：目標 Google 試算表 ID
// ACCESS_KEY：自行產生的連線密碼
const SCRIPT_PROPERTIES = PropertiesService.getScriptProperties();
const SPREADSHEET_ID = SCRIPT_PROPERTIES.getProperty('SPREADSHEET_ID');
const ACCESS_KEY = SCRIPT_PROPERTIES.getProperty('ACCESS_KEY');

const HEADERS = [
  '作文編號',
  '學生姓名',
  '年級',
  '作文題目',
  '教學目標',
  '作文內容',
  '狀態',
  '我的評語',
  '分數',
  '更新時間'
];

function doGet(e) {
  try {
    checkKey_(e.parameter.key);
    const action = e.parameter.action || 'list';
    if (action !== 'list') throw new Error('不支援這個讀取動作');
    return output_({ ok: true, essays: listEssays_() }, e.parameter.callback);
  } catch (error) {
    return output_({ ok: false, error: error.message }, e && e.parameter && e.parameter.callback);
  }
}

function doPost(e) {
  try {
    checkKey_(e.parameter.key);
    const action = e.parameter.action || 'save';
    const lock = LockService.getScriptLock();
    lock.waitLock(15000);
    try {
      if (action === 'create') {
        return output_({ ok: true, essay: createEssay_(e.parameter) });
      }
      if (action === 'save') {
        return output_({ ok: true, essay: saveReview_(e.parameter) });
      }
      if (action === 'upsert') {
        return output_({ ok: true, essay: upsertEssay_(e.parameter) });
      }
      throw new Error('不支援這個儲存動作');
    } finally {
      lock.releaseLock();
    }
  } catch (error) {
    return output_({ ok: false, error: error.message });
  }
}

function upsertEssay_(data) {
  const sheet = getSheet_();
  const id = clean_(data.id);
  if (!id) throw new Error('找不到作文編號');

  const student = clean_(data.student);
  const grade = clean_(data.grade);
  const title = clean_(data.title);
  const goal = clean_(data.goal);
  const content = String(data.content || '').trim();
  const status = ['待批改', '批改中', '已完成'].includes(data.status)
    ? data.status
    : '批改中';
  const comment = String(data.comment || '').trim();
  const score = data.score === '' || data.score == null ? '' : Number(data.score);

  if (!student || !grade || !title || !content) {
    throw new Error('學生姓名、年級、作文題目和作文內容都要填寫');
  }
  if (score !== '' && (!Number.isFinite(score) || score < 0 || score > 10)) {
    throw new Error('分數必須是 0 到 10');
  }

  const row = [
    id, student, grade, title, goal, content,
    status, comment, score, new Date()
  ];
  const lastRow = sheet.getLastRow();
  let rowNumber = 0;
  if (lastRow >= 2) {
    const ids = sheet.getRange(2, 1, lastRow - 1, 1).getDisplayValues().flat();
    const offset = ids.findIndex((value) => String(value).trim() === id);
    if (offset >= 0) rowNumber = offset + 2;
  }

  if (rowNumber) {
    sheet.getRange(rowNumber, 1, 1, HEADERS.length).setValues([row]);
  } else {
    sheet.appendRow(row);
  }

  return { id: id, status: status, comment: comment, score: score };
}

function listEssays_() {
  const sheet = getSheet_();
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];

  return sheet.getRange(2, 1, lastRow - 1, HEADERS.length).getValues()
    .map((row) => ({
      id: String(row[0] || '').trim(),
      student: String(row[1] || '').trim(),
      grade: String(row[2] || '').trim(),
      title: String(row[3] || '').trim(),
      goal: String(row[4] || '').trim(),
      content: String(row[5] || '').trim(),
      status: String(row[6] || '待批改').trim(),
      comment: String(row[7] || ''),
      score: row[8] === '' ? '' : Number(row[8]),
      updatedAt: row[9] instanceof Date ? row[9].toISOString() : String(row[9] || '')
    }))
    .filter((essay) => essay.id || essay.student || essay.title || essay.content);
}

function createEssay_(data) {
  const sheet = getSheet_();
  const id = 'ESSAY-' + Utilities.getUuid().slice(0, 8).toUpperCase();
  const essay = {
    id: id,
    student: clean_(data.student),
    grade: clean_(data.grade),
    title: clean_(data.title),
    goal: clean_(data.goal),
    content: String(data.content || '').trim(),
    status: '待批改',
    comment: '',
    score: '',
    updatedAt: new Date()
  };

  if (!essay.student || !essay.grade || !essay.title || !essay.content) {
    throw new Error('學生姓名、年級、作文題目和作文內容都要填寫');
  }

  sheet.appendRow([
    essay.id, essay.student, essay.grade, essay.title, essay.goal,
    essay.content, essay.status, essay.comment, essay.score, essay.updatedAt
  ]);
  return essay;
}

function saveReview_(data) {
  const sheet = getSheet_();
  const id = clean_(data.id);
  if (!id) throw new Error('找不到作文編號');

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) throw new Error('試算表裡還沒有作文');
  const ids = sheet.getRange(2, 1, lastRow - 1, 1).getDisplayValues().flat();
  const offset = ids.findIndex((value) => String(value).trim() === id);
  if (offset < 0) throw new Error('找不到這篇作文，請重新整理');

  const rowNumber = offset + 2;
  const status = ['待批改', '批改中', '已完成'].includes(data.status) ? data.status : '批改中';
  const comment = String(data.comment || '').trim();
  const score = data.score === '' || data.score == null ? '' : Number(data.score);
  if (score !== '' && (!Number.isFinite(score) || score < 0 || score > 10)) {
    throw new Error('分數必須是 0 到 10');
  }

  sheet.getRange(rowNumber, 7, 1, 4).setValues([[
    status,
    comment,
    score,
    new Date()
  ]]);

  return { id: id, status: status, comment: comment, score: score };
}

function getSheet_() {
  const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = spreadsheet.getSheetByName(SHEET_NAME);

  if (!sheet) {
    const firstSheet = spreadsheet.getSheets()[0];
    if (firstSheet && firstSheet.getLastRow() === 0) {
      firstSheet.setName(SHEET_NAME);
      sheet = firstSheet;
    } else {
      sheet = spreadsheet.insertSheet(SHEET_NAME);
    }
  }

  const currentHeaders = sheet.getRange(1, 1, 1, HEADERS.length).getDisplayValues()[0];
  const headersAreDifferent = HEADERS.some((header, index) => currentHeaders[index] !== header);
  if (headersAreDifferent) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }

  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, HEADERS.length)
    .setBackground('#2f6b53')
    .setFontColor('#ffffff')
    .setFontWeight('bold')
    .setHorizontalAlignment('center');
  sheet.getRange('F:F').setWrap(true);
  sheet.getRange('H:H').setWrap(true);
  sheet.setColumnWidth(1, 120);
  sheet.setColumnWidth(2, 100);
  sheet.setColumnWidth(3, 110);
  sheet.setColumnWidth(4, 180);
  sheet.setColumnWidth(5, 220);
  sheet.setColumnWidth(6, 420);
  sheet.setColumnWidth(7, 90);
  sheet.setColumnWidth(8, 420);
  sheet.setColumnWidth(9, 70);
  sheet.setColumnWidth(10, 150);
  return sheet;
}

function checkKey_(key) {
  if (key !== ACCESS_KEY) throw new Error('連線密碼不正確');
}

function clean_(value) {
  return String(value || '').trim();
}

function output_(data, callback) {
  const json = JSON.stringify(data);
  if (callback && /^[A-Za-z_$][0-9A-Za-z_$\.]*$/.test(callback)) {
    return ContentService.createTextOutput(callback + '(' + json + ');')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService.createTextOutput(json)
    .setMimeType(ContentService.MimeType.JSON);
}
