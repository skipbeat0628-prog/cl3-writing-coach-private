import sys
import unittest
import zipfile
from io import BytesIO
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import extract_imported_article


class ArticleImportTests(unittest.TestCase):
    def test_utf8_text_import(self):
        result = extract_imported_article("我的文章.txt", "第一段\n\n第二段".encode("utf-8"))
        self.assertEqual(result["title"], "我的文章")
        self.assertEqual(result["content"], "第一段\n\n第二段")

    def test_big5_text_import(self):
        result = extract_imported_article("作文.txt", "放學回家".encode("big5"))
        self.assertEqual(result["content"], "放學回家")

    def test_docx_import_keeps_paragraphs(self):
        document = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body><w:p><w:r><w:t>第一段</w:t></w:r></w:p><w:p><w:r><w:t>第二段</w:t></w:r></w:p></w:body>
        </w:document>'''.encode("utf-8")
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("word/document.xml", document)
        result = extract_imported_article("學生作文.docx", buffer.getvalue())
        self.assertEqual(result["title"], "學生作文")
        self.assertEqual(result["content"], "第一段\n\n第二段")

    def test_unsupported_format_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "只支援"):
            extract_imported_article("essay.pdf", b"not a pdf")


if __name__ == "__main__":
    unittest.main()
