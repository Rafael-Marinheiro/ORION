from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from app.validators import LetterAndDigitPasswordValidator


class LetterAndDigitPasswordValidatorTest(SimpleTestCase):
    def setUp(self):
        self.validator = LetterAndDigitPasswordValidator()

    def test_password_with_letter_and_digit_is_valid(self):
        for password in ["abc1", "1xyz", "Pass1234"]:
            self.validator.validate(password)

    def test_password_missing_letter_or_digit_is_invalid(self):
        for password in ["abcdef", "123456", "!!!!", "abcd!", "1234!"]:
            with self.assertRaises(ValidationError):
                self.validator.validate(password)
