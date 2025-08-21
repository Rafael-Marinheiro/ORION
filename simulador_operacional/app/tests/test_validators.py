import pytest
from django.core.exceptions import ValidationError

from app.validators import LetterAndDigitPasswordValidator


validator = LetterAndDigitPasswordValidator()


@pytest.mark.parametrize(
    "password",
    ["abc1", "1xyz", "Pass1234"],
)
def test_password_with_letter_and_digit_is_valid(password):
    validator.validate(password)


@pytest.mark.parametrize(
    "password",
    ["abcdef", "123456", "!!!!", "abcd!", "1234!"],
)
def test_password_missing_letter_or_digit_is_invalid(password):
    with pytest.raises(ValidationError):
        validator.validate(password)
