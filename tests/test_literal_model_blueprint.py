import unittest

from aind_pydantic_codegen.generators import LiteralModelBlueprint


class LiteralModelBlueprintTest(unittest.TestCase):
    def test_initialization(self):
        blueprint = LiteralModelBlueprint("my_mock_type")
        self.assertEqual(blueprint.class_name, "my_mock_type")
        self.assertEqual(blueprint.sanitized_class_name, "MyMockType")
        self.assertEqual(blueprint.code_builder, "")


if __name__ == "__main__":
    unittest.main()
