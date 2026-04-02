"""
Hack-n-TAP — Functional Tests
Testes funcionais simples para rodar em pre-commit / CI.
"""

import unittest
import os
import tempfile

from tap.model.database import SQLiteDatabase


class TestDatabaseSetup(unittest.TestCase):
    """Verifica que o banco inicializa corretamente."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = SQLiteDatabase(db_file=self.tmp.name)

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.tmp.name)

    def test_tables_exist(self):
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        self.assertIn("tags", tables)
        self.assertIn("history", tables)
        self.assertIn("admins", tables)

    def test_admin_initialized(self):
        self.assertTrue(self.db.check_credentials("admin", "tijolo22"))

    def test_invalid_credentials(self):
        self.assertFalse(self.db.check_credentials("admin", "wrongpass"))
        self.assertFalse(self.db.check_credentials("nobody", "tijolo22"))


class TestTagCRUD(unittest.TestCase):
    """Testa cadastro, leitura e remoção de tags."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = SQLiteDatabase(db_file=self.tmp.name)

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.tmp.name)

    def test_add_and_validate_tag(self):
        ok, msg = self.db.add_tag("ABC123", "Gaspar")
        self.assertTrue(ok)

        data = self.db.validate_tag("ABC123")
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "Gaspar")

    def test_duplicate_tag_rejected(self):
        self.db.add_tag("ABC123", "Gaspar")
        ok, msg = self.db.add_tag("ABC123", "Outro")
        self.assertFalse(ok)

    def test_validate_unknown_tag(self):
        self.assertIsNone(self.db.validate_tag("INEXISTENTE"))

    def test_get_all_tags(self):
        self.db.add_tag("T1", "Alice")
        self.db.add_tag("T2", "Bob")
        tags = self.db.get_all_tags()
        self.assertEqual(len(tags), 2)
        self.assertIn("T1", tags)
        self.assertIn("T2", tags)

    def test_update_tag_name(self):
        self.db.add_tag("T1", "Alice")
        ok, _ = self.db.update_tag("T1", "Alice Atualizada")
        self.assertTrue(ok)
        data = self.db.validate_tag("T1")
        self.assertEqual(data["name"], "Alice Atualizada")

    def test_remove_tag(self):
        self.db.add_tag("T1", "Alice")
        ok, _ = self.db.remove_tag("T1")
        self.assertTrue(ok)
        self.assertIsNone(self.db.validate_tag("T1"))


class TestHistory(unittest.TestCase):
    """Testa registro e consulta de histórico."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = SQLiteDatabase(db_file=self.tmp.name)

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.tmp.name)

    def test_add_history_entry(self):
        self.db.add_history_entry("T1", "Alice")
        entries = self.db.get_history_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "Alice")
        self.assertEqual(entries[0]["tag_id"], "T1")

    def test_history_order_desc(self):
        self.db.add_history_entry("T1", "Alice")
        self.db.add_history_entry("T2", "Bob")
        entries = self.db.get_history_entries()
        # Most recent first
        self.assertEqual(entries[0]["name"], "Bob")
        self.assertEqual(entries[1]["name"], "Alice")

    def test_empty_history(self):
        entries = self.db.get_history_entries()
        self.assertEqual(len(entries), 0)


class TestImports(unittest.TestCase):
    """Verifica que os imports do pacote funcionam."""

    def test_import_main(self):
        from tap.main import main
        self.assertTrue(callable(main))

    def test_import_database(self):
        from tap.model.database import SQLiteDatabase
        self.assertTrue(callable(SQLiteDatabase))

    def test_import_package(self):
        import tap
        self.assertIsNotNone(tap)


if __name__ == "__main__":
    unittest.main()
