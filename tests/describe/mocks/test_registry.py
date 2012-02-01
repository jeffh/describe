from unittest import TestCase

from mock import Mock, patch

from describe.mock.registry import StubRegistry


class TestStubRegistry(TestCase):
    def test_starts_with_no_registries(self):
        self.assertEqual(StubRegistry.registries, [])

    def test_creating_registries_add_to_master_list(self):
        n = len(StubRegistry.registries)
        reg = StubRegistry()
        self.assertEqual(len(StubRegistry.registries), n + 1)

        reg.destroy()
        self.assertEqual(len(StubRegistry.registries), n)

    def test_add_and_remove_stubs(self):
        s = Mock()
        reg = StubRegistry()
        reg.add(s)
        reg.add(s)
        self.assertEqual(reg.stubs, [s])

        reg.remove(s)
        self.assertEqual(reg.stubs, [])
        reg.destroy()

    def test_invoking_post_verify_hook(self):
        fn = Mock()
        reg = StubRegistry()
        reg.add_post_verify_hook(fn)
        reg.verify_mocks()
        reg.destroy()

        fn.assert_called_once_with()

