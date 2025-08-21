from django.test import TestCase, override_settings
from app.forms import MembroFormSet


@override_settings(MIGRATION_MODULES={"app": None})
class MembroFormSetTest(TestCase):
    def _build_data(self, total):
        data = {
            "form-TOTAL_FORMS": str(total),
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "3",
            "form-MAX_NUM_FORMS": "6",
        }
        for i in range(total):
            data[f"form-{i}-nome"] = f"U{i}"
            data[f"form-{i}-email"] = f"u{i}@example.com"
            data[f"form-{i}-senha"] = "pass"
            if i == 0:
                data[f"form-{i}-lider"] = "on"
        return data

    def test_invalid_member_count(self):
        formset = MembroFormSet(self._build_data(2))
        self.assertFalse(formset.is_valid())

    def test_invalid_member_count_too_many(self):
        formset = MembroFormSet(self._build_data(7))
        self.assertFalse(formset.is_valid())

    def test_valid_member_count(self):
        formset = MembroFormSet(self._build_data(3))
        self.assertTrue(formset.is_valid())
