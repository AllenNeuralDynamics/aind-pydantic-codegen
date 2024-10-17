import os
import unittest

from aind_pydantic_codegen.helpers import (
    count_indent_level,
    create_enum_key_from_class_name,
    indent_block,
    indent_line,
    is_pascal_case,
    normalize_model_source_provenance,
    replace_tabs_with_spaces,
    sanitize_class_name,
    to_pascal_case,
    unindent,
)


class PascalCaseTests(unittest.TestCase):
    class PascalCaseTests(unittest.TestCase):
        def test_is_pascal_case_true(self):
            self.assertTrue(is_pascal_case("PascalCase"))
            self.assertTrue(is_pascal_case("AnotherExample"))

        def test_is_pascal_case_false(self):
            self.assertFalse(is_pascal_case("notPascalCase"))
            self.assertFalse(is_pascal_case("another_example"))
            self.assertFalse(is_pascal_case(""))

        def test_to_pascal_case(self):
            self.assertEqual(to_pascal_case("pascal_case"), "PascalCase")
            self.assertEqual(to_pascal_case("another_example"), "AnotherExample")
            self.assertEqual(to_pascal_case("alreadyPascalCase"), "AlreadyPascalCase")
            self.assertEqual(to_pascal_case(""), "")


class IndentationTests(unittest.TestCase):
    class IndentationTests(unittest.TestCase):
        def test_count_indent_level(self):
            self.assertEqual(count_indent_level("\t\tIndented text"), 2)
            self.assertEqual(count_indent_level("No indent"), 0)
            self.assertEqual(count_indent_level("\tSingle indent"), 1)
            self.assertEqual(count_indent_level(""), 0)

        def test_replace_tabs_with_spaces(self):
            self.assertEqual(replace_tabs_with_spaces("\tIndented text"), "    Indented text")
            self.assertEqual(replace_tabs_with_spaces("\t\tDouble indented text"), "        Double indented text")
            self.assertEqual(replace_tabs_with_spaces("No indent"), "No indent")
            self.assertEqual(replace_tabs_with_spaces(""), "")

        def test_indent_block(self):
            self.assertEqual(indent_block("Line1\nLine2", 1), "\tLine1\n\tLine2\n")
            self.assertEqual(indent_block("Line1\nLine2", 2), "\t\tLine1\n\t\tLine2\n")
            self.assertEqual(indent_block("Line1\nLine2", 0), "Line1\nLine2\n")
            self.assertEqual(indent_block("", 1), "\t\n")

        def test_unindent(self):
            self.assertEqual(unindent("    Line1\n    Line2"), "Line1\nLine2")
            self.assertEqual(unindent("  Line1\n    Line2"), "Line1\n  Line2")
            self.assertEqual(unindent("Line1\nLine2"), "Line1\nLine2")
            self.assertEqual(unindent(""), "")

        def test_indent_line(self):
            self.assertEqual(indent_line("Line1", 1), "\tLine1")
            self.assertEqual(indent_line("Line1", 2), "\t\tLine1")
            self.assertEqual(indent_line("Line1", 0), "Line1")
            with self.assertRaises(ValueError):
                indent_line("Line1", -1)


class SanitizeClassNameTests(unittest.TestCase):
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


class NormalizeModelSourceProvenanceTests(unittest.TestCase):
    def test_normalize_model_source_provenance_with_string(self):
        self.assertEqual(normalize_model_source_provenance("some_string"), "some_string")

    def test_normalize_model_source_provenance_with_pathlike(self):
        self.assertEqual(normalize_model_source_provenance(os.path.join("some", "path")), os.path.join("some", "path"))


class CreateEnumKeyFromClassNameTests(unittest.TestCase):
    def test_create_enum_key_from_class_name(self):
        self.assertEqual(create_enum_key_from_class_name("MyClassName"), "MYCLASSNAME")
        self.assertEqual(create_enum_key_from_class_name("my_class_name"), "MY_CLASS_NAME")
        self.assertEqual(create_enum_key_from_class_name("My-Class-Name"), "MY_CLASS_NAME")
        self.assertEqual(create_enum_key_from_class_name("My Class Name"), "MY_CLASS_NAME")
        self.assertEqual(create_enum_key_from_class_name("9MyClassName"), "_9MYCLASSNAME")
        self.assertEqual(create_enum_key_from_class_name("_MyClassName"), "__MYCLASSNAME")
        self.assertEqual(create_enum_key_from_class_name("9"), "_9")

        with self.assertRaises(ValueError):
            create_enum_key_from_class_name("")


if __name__ == "__main__":
    unittest.main()
