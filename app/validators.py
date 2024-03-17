from django.core.validators import EmailValidator, ValidationError
from django.utils.encoding import punycode


class CustomEmailValidator(EmailValidator):
    """
    Email validator for block ru and by emails
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invalid_emails = [".ru", ".by"]
        self.message = "login__email"

    def __call__(self, value):
        if not value or "@" not in value:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        user_part, domain_part = value.rsplit("@", 1)

        if not self.user_regex.match(user_part):
            raise ValidationError(self.message, code=self.code, params={"value": value})

        if any(domain_part.endswith(invalid_domain) for invalid_domain in self.invalid_emails):
            raise ValidationError("ru__email", code=self.code, params={"value": value})

        if domain_part not in self.domain_allowlist and not self.validate_domain_part(
                domain_part
        ):
            # Try for possible IDN domain-part
            try:
                domain_part = punycode(domain_part)
            except UnicodeError:
                pass
            else:
                if self.validate_domain_part(domain_part):
                    return
            raise ValidationError(self.message, code=self.code, params={"value": value})


validate_email = EmailValidator()