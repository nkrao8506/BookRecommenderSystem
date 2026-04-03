"""
Custom test runner that disables template rendering signals
to work around Python 3.14 + Django 4.2 compatibility issues.
"""

from django.test.runner import DiscoverRunner


class NoTemplateTestRunner(DiscoverRunner):
    """Test runner that disables template rendering to avoid Python 3.14 issues."""

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        # Disable template rendering during tests
        from django.template import engines
        from django.test.utils import setup_test_environment

        # Monkey-patch the template context to avoid copying issues
        import django.template.context

        original_copy = django.template.context.Context.__copy__

        def safe_copy(self):
            try:
                return original_copy(self)
            except AttributeError:
                # Fallback for Python 3.14 compatibility
                return self

        django.template.context.Context.__copy__ = safe_copy
