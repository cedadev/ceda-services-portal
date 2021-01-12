"""
This module provides custom validators.
"""

__author__ = "Matt Pryor"
__copyright__ = "Copyright 2015 UK Science and Technology Facilities Council"

import re

from sshpubkeys import SSHKey, InvalidKeyException

from django.core.exceptions import ValidationError


def validate_ssh_key(value):
    """
    Tests if the given value is a valid SSH key.
    """
    # We are not in the business of validating presence...
    if not value: return
    # Make sure there are no newlines
    lines = value.splitlines()
    if len(lines) > 1:
        raise ValidationError('SSH key must not contain new lines')
    # Try to parse the SSH key
    key = SSHKey(strict_mode = False)
    try:
        key.parse(lines[0])
    except InvalidKeyException:
        raise ValidationError('Not a valid SSH public key')
    else:
        reason = None
        if key.key_type != b'ssh-rsa':
            reason = '({} key given)'.format(key.key_type.decode('utf-8'))
        elif key.bits < 2048:
            reason = '({} bits given)'.format(key.bits)
        if reason:
            raise ValidationError('Please use an RSA key of at least 2048 bits {}'.format(reason))


class ComplexPasswordValidator:
    """
    Django password validator that ensures passwords contain at least one each of:
      * Lower-case letter
      * Upper-case letter
      * Number
      * Non-alphanumeric
    """
    #: The list of regexes that must pass with a message for each
    patterns = (
        ('[a-z]', 'Password must contain a lower-case letter'),
        ('[A-Z]', 'Password must contain an upper-case letter'),
        ('\d', 'Password must contain a number'),
        ('[^\w]', 'Password must contain a symbol'),
    )

    def validate(self, password, user = None):
        errors = [
            ValidationError(msg)
            for regex, msg in self.patterns
            if re.search(regex, password) is None
        ]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return ('Your password must contain a lower-case letter, an upper-case letter, '
                'a number and a symbol.')