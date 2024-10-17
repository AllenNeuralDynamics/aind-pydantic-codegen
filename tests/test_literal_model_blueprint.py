import unittest

from aind_pydantic_codegen.generators import LiteralModelBlueprint
from aind_pydantic_codegen.helpers import sanitize_class_name


class LiteralModelBlueprintTest(unittest.TestCase):
    def test_sanitize_class_name(self):
        self.assertEqual(sanitize_class_name("My_Mock_Type"), "MyMockType")
        self.assertEqual(sanitize_class_name("my_mock_type"), "MyMockType")
        self.assertEqual(sanitize_class_name("MyMockType"), "Mymocktype")
        self.assertEqual(sanitize_class_name("My Mock Type"), "MyMockType")
        self.assertEqual(sanitize_class_name("My-Mock-Type"), "MyMockType")
        self.assertEqual(sanitize_class_name("9MyMockType"), "_9mymocktype")
        self.assertEqual(sanitize_class_name("9 My Mock Type"), "_9MyMockType")
        self.assertEqual(sanitize_class_name("9-My-Mock-Type"), "_9MyMockType")
        self.assertEqual(sanitize_class_name("_MyMockType"), "_Mymocktype")

    def test_initialization(self):
        blueprint = LiteralModelBlueprint("my_mock_type")
        self.assertEqual(blueprint.class_name, "my_mock_type")
        self.assertEqual(blueprint.sanitized_class_name, "MyMockType")
        self.assertEqual(blueprint.code_builder, "")


if __name__ == "__main__":
    unittest.main()
