import unittest
from mock import MagicMock, patch
from viewstate import ViewState, ViewStateManager, split_and_validate_path, get_default_viewstate
from helio.controller.base import BaseViewController
from helio.helio_exceptions import ViewStateError


class TestViewStateFunctions(unittest.TestCase):
    def test_path_with_invalid_root(self):
        """ValueError is raised when validating a path that doesn't start with 'page.'"""
        self.assertRaises(ValueError, split_and_validate_path, 'component.child-component')

    def test_path_with_blank_compoents(self):
        """ValueError is raised when validating a path that has blank components (i.e. '..' in the path)"""
        self.assertRaises(ValueError, split_and_validate_path, 'page.component..child-component')

    def test_path_split(self):
        self.assertEqual(split_and_validate_path('page.test.path.one.two.three'),
                         (['page', 'test', 'path', 'one', 'two', 'three']))

    def test_default_viewstate_generator(self):
        """get_default_viewstate should return a ViewState instance."""
        vs = get_default_viewstate()
        self.assertIsInstance(vs, ViewState)


class TestViewStateClass(unittest.TestCase):
    def setUp(self):
        self.root_controller = BaseViewController()
        self.child_one = BaseViewController()
        self.child_two = BaseViewController()
        self.child_three = BaseViewController()

        self.vs = ViewState(self.root_controller)
        self.root_controller.set_child('one', self.child_one)
        self.child_one.set_child('two', self.child_two)
        self.child_two.set_child('three', self.child_three)

    def test_view_state_init(self):
        """A ViewState can only be inited with a root controller arg."""
        with self.assertRaises(TypeError):
            ViewState()

    def test_root_view_set(self):
        """Initing the ViewState sets the root controller to the root_controller attribute."""
        root_controller = MagicMock()
        vs = ViewState(root_controller)
        self.assertEqual(vs.root_controller, root_controller)

    def test_component_path_retrieval(self):
        """A component can be retrieved from the tree by its path."""
        self.assertEqual(self.vs.controller_from_path('page'), self.root_controller)
        self.assertEqual(self.vs.controller_from_path('page.one'), self.child_one)
        self.assertEqual(self.vs.controller_from_path('page.one.two'), self.child_two)
        self.assertEqual(self.vs.controller_from_path('page.one.two.three'), self.child_three)

    def test_root_component_insert_error(self):
        """Inserting a component at path 'page' is invalid and raises a ValueError."""
        new_component = BaseViewController
        self.assertRaises(ValueError, self.vs.insert_controller, 'page', new_component)

    def test_component_path_insert(self):
        """A component can be inserted directly using a path, replacing the existing stack there."""
        new_component = BaseViewController()
        self.child_one.set_child = MagicMock()
        self.vs.insert_controller('page.one.four', new_component)
        self.child_one.set_child.assert_called_with('four', new_component)

    def test_new_component_path_insert(self):
        """A new controller can be instantiated (based on component name) and then can be inserted directly using a view
        path, replacing the existing stack there."""
        new_component = MagicMock()
        self.vs.insert_controller = MagicMock()
        with patch('helio.viewstate.viewstate.init_controller', return_value=new_component) as patched_init:
            self.vs.insert_new_controller('page.one.four', 'new.component.path', 'arg1', 'arg2', kwarg1='kwarg1',
                                         kwarg2='kwarg2')
            patched_init.assert_called_with('new.component.path', 'arg1', 'arg2', kwarg1='kwarg1', kwarg2='kwarg2')
            self.vs.insert_controller.assert_called_with('page.one.four', new_component)

    def test_component_path_push(self):
        """A component can be pushed onto the stack at a path."""
        new_component = MagicMock()
        self.child_one.push_child = MagicMock()
        self.vs.push_controller('page.one.four', new_component)
        self.child_one.push_child.assert_called_with('four', new_component)

    def test_new_component_path_push(self):
        """A new controller can be instantiated (based on component name) and then can be pushed directly using a view
        path, onto the stack there."""
        new_component = MagicMock()
        self.vs.push_controller = MagicMock()
        with patch('helio.viewstate.viewstate.init_controller', return_value=new_component) as patched_init:
            self.vs.push_new_controller('page.one.four', 'new.component.path', 'arg1', 'arg2', kwarg1='kwarg1',
                                         kwarg2='kwarg2')
            patched_init.assert_called_with('new.component.path', 'arg1', 'arg2', kwarg1='kwarg1', kwarg2='kwarg2')
            self.vs.push_controller.assert_called_with('page.one.four', new_component)

    def test_component_path_pop(self):
        """A component can be popped from the stack by giving its path to the ViewState."""
        # tree looks like this -> page.one.two.three
        self.child_two.pop_child = MagicMock(return_value=self.child_three)
        self.child_one.pop_child = MagicMock(return_value=self.child_two)

        child_three = self.vs.pop_controller('page.one.two.three')
        child_two = self.vs.pop_controller('page.one.two')

        self.assertEqual(self.child_three, child_three)
        self.assertEqual(self.child_two, child_two)
        self.child_two.pop_child.assert_called_with('three')
        self.child_one.pop_child.assert_called_with('two')

    def test_page_pop_fails(self):
        """ValueError is raised when trying to pop the root (page)."""
        self.assertRaises(ValueError, self.vs.pop_controller, 'page')


class TestViewStateManagerClass(unittest.TestCase):
    def setUp(self):
        self.vsm = ViewStateManager()

    def test_viewstate_creation_on_empty(self):
        """Get VS with None id (when no viewstates exist) should create a VS and return it and its index."""
        vs = self.vsm.get_view_state(None)
        self.assertEqual(vs.index, 0)
        self.assertIsInstance(vs, ViewState)

    def test_viewstate_retrieval(self):
        """Get VS with an index that exists should return the VS at that index."""
        vs1 = self.vsm.get_view_state(None)
        vs2 = self.vsm.get_view_state(0)
        self.assertEqual(vs1.index, 0)
        self.assertEqual(vs1, vs2)

    def test_viewstate_unexpected_creation(self):
        """Retrieving a viewstate outside the VS range should create a new VS and return it and its index."""
        vs1 = self.vsm.get_view_state(None)
        vs2 = self.vsm.get_view_state(3)

        self.assertEqual(vs1.index, 0)
        self.assertEqual(vs2.index, 1)
        self.assertNotEqual(vs1, vs2)

    def test_viewstate_creation(self):
        """Get VS with None id should create a VS and return it and its index."""
        vs1 = self.vsm.get_view_state(None)
        vs2 = self.vsm.get_view_state(None)
        self.assertNotEqual(vs1, vs2)

    def test_viewstate_creation_no_create(self):
        """Get VS with invalid id should raise ViewStateError if no_create is True."""
        with self.assertRaises(ViewStateError):
            self.vsm.get_view_state(None, no_create=True)

        with self.assertRaises(ViewStateError):
            self.vsm.get_view_state(5, no_create=True)

    def test_negative_index_creation(self):
        """If the negative VS index is given, a new VS should be created (rather than using using it as a reverse
        index)."""
        vs = self.vsm.get_view_state(-1)
        self.assertEqual(vs.index, 0)
        vs = self.vsm.get_view_state(-1)
        self.assertEqual(vs.index, 1)
        vs = self.vsm.get_view_state(-2)
        self.assertEqual(vs.index, 2)


if __name__ == '__main__':
    unittest.main()