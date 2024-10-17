import unittest

from aind_pydantic_codegen.generators import ForwardClassReference, ModelGenerator

from . import MyMockType, mock_template_helper


class LocalClass:
    pass


class ModelGeneratorSolveImportsTest(unittest.TestCase):
    def setUp(self):
        self.builder = mock_template_helper
        self.import_builder = self.builder.import_statement

    def test_solve_imports_from_forward_class_reference(self):
        fwd_class_ref = ForwardClassReference("MyModule", "MyClass")
        import_str = ModelGenerator.solve_import(self.builder, fwd_class_ref)
        self.assertEqual(self.import_builder(fwd_class_ref.module_name, fwd_class_ref.class_name), import_str)

    def test_solve_imports_from_class(self):
        import_str = ModelGenerator.solve_import(self.builder, MyMockType)
        self.assertEqual(self.import_builder(MyMockType.__module__, MyMockType.__name__), import_str)

    def test_solve_imports_from_builtin(self):
        import_str = ModelGenerator.solve_import(self.builder, int)
        self.assertEqual("", import_str)

    def test_solve_imports_from_local(self):
        import_str = ModelGenerator.solve_import(
            self.builder, MyMockType, default_module_name="tests.test_model_generator"
        )
        self.assertEqual(self.import_builder("tests", "MyMockType"), import_str)

        import_str = ModelGenerator.solve_import(
            self.builder, LocalClass, default_module_name="tests.test_model_generator"
        )
        self.assertEqual(self.import_builder("tests.test_model_generator", "LocalClass"), import_str)

    def test_solve_imports_from_local_no_default_module_name(self):
        fwd_class_ref = ForwardClassReference("__main__", "MyClass")
        with self.assertRaises(ValueError):
            ModelGenerator.solve_import(self.builder, fwd_class_ref, default_module_name=None)


if __name__ == "__main__":
    unittest.main()
