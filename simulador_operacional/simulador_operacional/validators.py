import re
from django.core.exceptions import ValidationError

class NumberLetterPasswordValidator:
    def validate(self, password, user=None):
        if not re.search('[A-Za-z]', password) or not re.search('\\d', password):
            raise ValidationError(
                'A senha deve conter letras e números.',
                code='password_no_mix'
            )

    def get_help_text(self):
        return 'Sua senha deve conter pelo menos uma letra e um número.'
