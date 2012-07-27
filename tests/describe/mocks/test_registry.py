from unittest import TestCase

from mock import Mock, patch

from describe.mock.registry import Registry


class TestRegistry(TestCase):
    def test_starts_with_no_registries(self):
        self.assertEqual(Registry.registries, [])

    def test_creating_registries_add_to_master_list(self):
        n = len(Registry.registries)
        reg = Registry()
        self.assertEqual(len(Registry.registries), n + 1)

        reg.destroy()
        self.assertEqual(len(Registry.registries), n)

    def test_add_and_remove_stubs(self):
        s = Mock()
        reg = Registry()
        reg.add(s)
        reg.add(s)
        self.assertEqual(reg.stubs, [s])

        reg.remove(s)
        self.assertEqual(reg.stubs, [])
        reg.destroy()

    def test_invoking_post_verify_hook(self):
        fn = Mock()
        reg = Registry()
        reg.add_post_verify_hook(fn)
        reg.verify_mocks()
        reg.destroy()

        fn.assert_called_once_with()

