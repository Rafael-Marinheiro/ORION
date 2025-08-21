import re
from django.core.exceptions import ValidationError


class LetterAndDigitPasswordValidator:
    """Validate that the password has at least one letter and one digit."""

    def validate(self, password, user=None):
        if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
            raise ValidationError(
                "A senha deve conter ao menos uma letra e um dígito.",
                code="password_no_letter_or_digit",
            )

    def get_help_text(self):
        return "Sua senha deve conter ao menos uma letra e um dígito."
