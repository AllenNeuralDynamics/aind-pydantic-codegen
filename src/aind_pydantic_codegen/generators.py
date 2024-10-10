from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, Self, Type, TypeVar, Union

from pydantic import BaseModel

from . import helpers
from .formatters import CodeFormatter
from .helpers import TemplateHelper
from .validators import CodeValidator

TModel = TypeVar("TModel", bound=BaseModel)
TMapTo = TypeVar("TMapTo", bound=Union[Any])
AllowedSources = Union[os.PathLike[str], str]
ParsedSource = Dict[str, str]


@dataclass(eq=True, frozen=True)
class ForwardClassReference:
    """A record to store a forward reference to a class."""

    module_name: str
    class_name: str


@dataclass
class ParsedSourceKeyHandler:
    """Represents an object that can handle/transform a parsed field reference"""

    field: str
    function_handle: Optional[Callable[..., str]] = None


class MappableReferenceField(Generic[TMapTo]):
    """Represents a reference that can be mapped to a class"""

    def __init__(
        self,
        typeof: Type[TMapTo] | ForwardClassReference,  # Allow for types to be passed as string references
        pattern: str,
        field_name: str,
        parsed_source_keys_handlers: Optional[Union[List[str], List[ParsedSourceKeyHandler]]] = None,
    ) -> None:
        self._typeof = typeof
        self._pattern = pattern
        self._parsed_source_keys_handlers = self._normalize_parsed_source_keys(parsed_source_keys_handlers)
        self._field_name = field_name

    @staticmethod
    def _normalize_parsed_source_keys(
        handlers: Optional[Union[List[str], List[ParsedSourceKeyHandler]]],
    ) -> List[ParsedSourceKeyHandler]:
        """Ensures that all handlers are converted to a uniform type


        Args:
            handler (Optional[Union[List[str], List[ParsedSourceKeyHandler]]]): The optional array with all handlers to be used. If left None, an empty list will be returned.
        Raises:
            ValueError: An ValueError exception will be thrown if the input type is not valid.

        Returns:
            List[ParsedSourceKeyHandler]: Returns a list where all entries are ParsedSourceKeyHandler types.
        """
        _normalized: List[ParsedSourceKeyHandler] = []
        if handlers is None:
            return _normalized
        for handle in handlers:
            if isinstance(handle, str):
                _normalized.append(ParsedSourceKeyHandler(handle))
                break
            elif isinstance(handle, ParsedSourceKeyHandler):
                _normalized.append(handle)
            else:
                raise ValueError(f"Invalid type: {type(handle)}")
        return _normalized

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def parsed_source_keys(self) -> List[str]:
        return [value.field for value in self._parsed_source_keys_handlers]

    @property
    def typeof(self) -> Union[Type[TMapTo], ForwardClassReference]:
        return self._typeof

    @property
    def pattern(self) -> str:
        return self._pattern

    def __call__(self, parsed_source: ParsedSource) -> str:
        for key in self.parsed_source_keys:
            if key not in parsed_source:
                raise KeyError(f"Key not found in source data: {key}")
        _args: List[str] = []
        for value in self._parsed_source_keys_handlers:
            _args.append(
                value.function_handle(parsed_source[key]) if value.function_handle is not None else parsed_source[key]
            )
        return self._pattern.format(*_args)

    def has_mappable_field(self, obj: Any) -> bool:
        return hasattr(obj, self.field_name)


@dataclass
class _WrappedModelGenerator:
    model_generator: ModelGenerator
    target_path: Optional[os.PathLike[str]] = None


class GeneratorContext:
    """
    A singleton class that manages multiple model generators, allowing for their centralized management
    and code generation. This context ensures that only one instance exists throughout the application,
    which can be used to add, remove, and generate code from multiple model generators.

    Attributes:
        _self (GeneratorContext): A private class-level attribute that holds the singleton instance.
        _initialized (bool): A flag indicating whether the instance has been initialized.
        _generators (List[_WrappedModelGenerator]): A list of wrapped model generators managed by this context.
        code_validators (List[CodeValidator]): A list of validators to check the generated code.
        code_formatters (List[CodeFormatter]): A list of formatters to apply to the generated code.

    Methods:
        __new__(cls) -> Self: Controls the creation of the singleton instance of the class.
        __init__(code_validators: Optional[List[CodeValidator]] = None,
                 code_formatters: Optional[List[CodeFormatter]] = None) -> None:
            Initializes the generator context, creating an empty list of generators and accepting optional
            code validators and formatters.

        generators() -> List[ModelGenerator]:
            Returns a list of model generators contained in this context.

        add_generator(generator: ModelGenerator,
                      file_name: Optional[os.PathLike[str]] = None):
            Adds a new model generator to the context, optionally associating it with a file name.

        remove_generator(generator: ModelGenerator):
            Removes a model generator from the context.

        generate_all() -> List[str]:
            Generates code for all model generators managed by this context and returns a list of the generated code.

        write_all(output_folder: os.PathLike = Path("."),
                  create_dir: bool = True):
            Writes the generated code from all model generators to specified files in the output folder.

        __enter__() -> Self:
            Supports the context manager protocol, returning the current instance.

        __exit__(self, exc_type, exc_value, traceback) -> None:
            Cleans up the context when exiting, resetting internal state.

    Raises:
        ValueError: If any issues arise during generator management or code generation.
    """

    _self = None
    _initialized = False

    def __new__(cls, *args, **kwargs) -> Self:
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(
        self,
        code_validators: Optional[List[CodeValidator]] = None,
        code_formatters: Optional[List[CodeFormatter]] = None,
    ) -> None:
        if not self._initialized:  # Check if the instance has been initialized
            self._generators: List[_WrappedModelGenerator] = []
            self.code_validators = code_validators or []
            self.code_formatters = code_formatters or []
            self._initialized = True

    @property
    def generators(self) -> List[ModelGenerator]:
        return [g.model_generator for g in self._generators]

    def add_generator(self, generator: ModelGenerator, file_name: Optional[os.PathLike[str]] = None):
        self._generators.append(_WrappedModelGenerator(model_generator=generator, target_path=file_name))

    def remove_generator(self, generator: ModelGenerator):
        self._generators = [g for g in self._generators if g.model_generator != generator]

    def generate_all(self) -> List[str]:
        return [
            generator.model_generator.generate(
                code_validators=self.code_validators, code_formatters=self.code_formatters
            )
            for generator in self._generators
        ]

    def write_all(self, output_folder: os.PathLike = Path("."), create_dir: bool = True):
        if create_dir:
            os.makedirs(output_folder, exist_ok=True)

        for generator in self._generators:
            target_path = (
                generator.target_path
                if generator.target_path
                else generator.model_generator.enum_like_class_name.lower() + ".py"
            )
            generator.model_generator.write(
                Path(output_folder) / str(target_path),
                code_validators=self.code_validators,
                code_formatters=self.code_formatters,
            )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._generators = []
        self._self = None
        self._initialized = False


@dataclass
class LiteralModelBlueprint:
    """
    Represents a blueprint for generating a literal model class. This blueprint holds the class name,
    a sanitized version of the class name, and a string that accumulates the generated code for the model.

    Attributes:
        class_name (str): The original name of the literal model class.
        sanitized_class_name (str): A sanitized version of the class name, which is automatically
            generated during initialization to ensure it conforms to valid class name conventions.
        code_builder (str): A string that accumulates the code generated for the literal model class.
            This can be used to store the code for fields, methods, and other class definitions.

    Methods:
        __post_init__(): Automatically sanitizes the class name after initialization.
    """

    class_name: str
    sanitized_class_name: str = field(init=False)
    code_builder: str = ""

    def __post_init__(self):
        self.sanitized_class_name = helpers.sanitize_class_name(self.class_name)


class ModelGenerator:
    """
    A class responsible for generating Python code that defines models based on a parsed data source,
    typically using Pydantic's BaseModel. The generated models include literal fields, enum-like classes,
    and optional validation or formatting steps.

    Args:
        class_name (str): The name of the enum-like class to be generated.
        seed_model_type (Type[TModel]): The seed model class that all literal classes will inherit from.
        data_source_identifier (AllowedSources): The identifier of the source of the data used for code generation.
        parser (Callable[..., List[ParsedSource]]): A callable function that parses the source data and returns a list of `ParsedSource` objects.
        discriminator (str, optional): The field used to differentiate between literal models in the enum-like class. Defaults to "name".
        literal_class_name_hints (Optional[list[str]], optional): A list of field names to hint at the class name from the source data. Defaults to `["abbreviation", "name"]`.
        preamble (Optional[str], optional): A string of additional code to include at the top of the generated file. Defaults to None.
        additional_imports (Optional[list[Type]], optional): A list of additional types to be imported in the generated code. Defaults to None.
        render_abbreviation_map (bool, optional): Whether to include a method that renders an abbreviation map in the enum-like class. Defaults to True.
        mappable_references (Optional[List[MappableReferenceField]], optional): A list of mappable reference fields to be used when generating the models. Defaults to None.
        default_module_name (str, optional): The default module name used when solving imports for types defined in the main script. Defaults to "aind_data_schema_models.generators".
        **kwargs: Additional keyword arguments passed to the model generator.

    Attributes:
        enum_like_class_name (str): The name of the generated enum-like class.
        _seed_model_type (Type[TModel]): The seed model class from which literal classes inherit.
        _data_source_identifier (AllowedSources): The identifier of the source of data used for code generation.
        _discriminator (str): The field used to distinguish between literal model types.
        _render_abbreviation_map (bool): Whether to generate the abbreviation map method in the enum-like class.
        _parser (Callable[..., List[ParsedSource]]): A function that parses the data source into a list of ParsedSource objects.
        _literal_class_name_hints (list[str]): A list of hints to help infer class names from the source data.
        _additional_imports (list[Type], optional): Additional types that need to be imported into the generated code.
        _additional_preamble (str, optional): Additional code to include in the preamble of the generated file.
        _mappable_references (List[MappableReferenceField], optional): Reference fields that map the source data to the generated models.
        _default_module_name (str): The default module name used for solving imports when '__main__' is returned as the module name.
        _parsed_source (List[ParsedSource]): The parsed source data used to generate the literal models.
        _literal_model_blueprints (List[LiteralModelBlueprint]): A list of blueprints for the generated literal models.

    Methods:
        solve_import(builder, typeof, default_module_name): Resolves the import statement for a given type or reference.
        generate(code_validators, code_formatters): Generates code for the models, applying validators and formatters if provided.
        write(output_path, code_validators, code_formatters): Writes the generated code to a specified file.
        generate_literal_model(cls, builder, parsed_source, seed_model_type, mappable_references, class_name, class_name_hints, require_all_fields_mapped):
            Generates a literal model blueprint based on parsed data.
        generate_enum_like_class(builder, class_name, discriminator, seed_model_type, literal_model_blueprints, render_abbreviation_map):
            Generates an enum-like class based on the literal models.
        parse(): Parses the data source using the provided parser function.
        _generate_mappable_references(): Generates import statements for the mappable references.
        _validate(): Validates the model class name, seed model type, and mappable references.
        _validate_class_name(class_name): Ensures the provided class name is in PascalCase.
    """

    _BUILDER = TemplateHelper()
    _DEFAULT_LITERAL_CLASS_NAME_HINTS = ["abbreviation", "name"]

    def __init__(
        self,
        class_name: str,
        seed_model_type: Type[TModel],
        data_source_identifier: AllowedSources,
        parser: Callable[..., List[ParsedSource]],
        discriminator: str = "name",
        literal_class_name_hints: Optional[list[str]] = None,
        preamble: Optional[str] = None,
        additional_imports: Optional[list[Type]] = None,
        render_abbreviation_map: bool = True,
        mappable_references: Optional[List[MappableReferenceField]] = None,
        default_module_name: str = "aind_data_schema_models.generators",
        **kwargs,
    ) -> None:
        self.enum_like_class_name = class_name
        self._seed_model_type = seed_model_type
        self._data_source_identifier = data_source_identifier
        self._discriminator = discriminator
        self._render_abbreviation_map = render_abbreviation_map
        self._parser = parser
        self._literal_class_name_hints = literal_class_name_hints or self._DEFAULT_LITERAL_CLASS_NAME_HINTS
        self._additional_imports = additional_imports
        self._additional_preamble = preamble
        self._mappable_references = mappable_references
        self._default_module_name = default_module_name

        self._parsed_source: List[ParsedSource] = self.parse()
        self._literal_model_blueprints: List[LiteralModelBlueprint] = []

        self._validate()

    @staticmethod
    def solve_import(
        builder: TemplateHelper, typeof: Type | ForwardClassReference, default_module_name: Optional[str] = None
    ) -> str:
        """Attempts to resolve the import statement for a given type or reference.

        Args:
            builder (TemplateHelper): An interface responsible for generating literal code.
            typeof (Type | ForwardClassReference): The type or forward reference to a type that needs to be imported.
            default_module_name (Optional[str], optional): The default module name to use if the module is resolved as '__main__'.
                If '__main__' is returned and no default module name is provided, a ValueError is raised. Defaults to None.

        Raises:
            ValueError: If the module name is '__main__' and no default module name is provided.

        Returns:
            str: A string representing the code required to import the type.
        """
        module_name: str
        class_name: str

        if isinstance(typeof, ForwardClassReference):
            module_name = typeof.module_name
            class_name = typeof.class_name
        elif isinstance(typeof, type):
            module_name = typeof.__module__
            class_name = typeof.__name__
        else:
            raise ValueError("typeof must be a type or ModuleReference")

        if module_name == "builtins":
            return ""
        if module_name == "__main__":
            if default_module_name is None:
                raise ValueError("Module name is '__main__' but not default value was provided to override")
            module_name = default_module_name

        return builder.import_statement(module_name=module_name, class_name=class_name)

    def generate(
        self,
        code_validators: Optional[List[CodeValidator]] = None,
        code_formatters: Optional[List[CodeFormatter]] = None,
    ) -> str:
        """Generates code and optionally applies validators and formatters.

        Args:
            code_validators (Optional[List[CodeValidator]], optional): A list of code validators to run.
                Defaults to None.
            code_formatters (Optional[List[CodeFormatter]], optional): A list of code formatters to apply.
                Defaults to None.

        Raises:
            error: If the code fails the validation check.

        Returns:
            str: The generated code, formatted and validated.
        """
        string_builder = "\n"

        for sub in self._parsed_source:
            class_blueprint = self.generate_literal_model(
                builder=self._BUILDER,
                parsed_source=sub,
                seed_model_type=self._seed_model_type,
                mappable_references=self._mappable_references,
                class_name_hints=self._literal_class_name_hints,
            )
            self._literal_model_blueprints.append(class_blueprint)

        string_builder += "\n\n".join([bp.code_builder for bp in self._literal_model_blueprints])

        string_builder += self.generate_enum_like_class(
            builder=self._BUILDER,
            class_name=self.enum_like_class_name,
            discriminator=self._discriminator,
            seed_model_type=self._seed_model_type,
            literal_model_blueprints=self._literal_model_blueprints,
            render_abbreviation_map=self._render_abbreviation_map,
        )

        generated_code = "".join(
            [
                self._BUILDER.file_header(helpers.normalize_model_source_provenance(self._data_source_identifier)),
                self._BUILDER.import_statements(),
                self._generate_mappable_references(),
                self.solve_import(self._BUILDER, self._seed_model_type, default_module_name=self._default_module_name),
                "".join(
                    [
                        self.solve_import(self._BUILDER, import_module, default_module_name=self._default_module_name)
                        for import_module in self._additional_imports
                    ]
                    if self._additional_imports
                    else []
                ),
                self._additional_preamble if self._additional_preamble else "",
                string_builder,
            ]
        )

        generated_code = helpers.unindent(generated_code)
        generated_code = helpers.replace_tabs_with_spaces(generated_code)

        if code_validators is not None:
            for validator in code_validators:
                is_valid, error = validator.validate(generated_code)
                if not is_valid:
                    raise error if error else ValueError("Generated code is not valid")

        if code_formatters is not None:
            for formatter in code_formatters:
                generated_code = formatter.format(generated_code)

        return generated_code

    def _generate_mappable_references(self) -> str:
        string_builder = ""
        if self._mappable_references is not None:
            refs = set([mappable.typeof for mappable in self._mappable_references])
            for ref in refs:
                string_builder += self.solve_import(self._BUILDER, ref, default_module_name=self._default_module_name)
        return string_builder

    def write(
        self,
        output_path: Union[os.PathLike, str],
        code_validators: Optional[List[CodeValidator]] = None,
        code_formatters: Optional[List[CodeFormatter]] = None,
    ):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.generate(code_validators=code_validators, code_formatters=code_formatters))

    @staticmethod
    def _validate_class_name(class_name: str) -> None:
        if not helpers.is_pascal_case(class_name):
            raise ValueError("model_name must be in PascalCase")

    def _validate(self):
        if not issubclass(self._seed_model_type, BaseModel):
            raise ValueError("model_type must be a subclass of pydantic.BaseModel")

        self._validate_class_name(self.enum_like_class_name)

        if self._mappable_references is not None:
            fields_name = [mappable.field_name for mappable in self._mappable_references]
            if len(fields_name) != len(set(fields_name)):
                raise ValueError(
                    f"field_name must be unique across all MappableReferenceField objects. Entries: {fields_name}"
                )

    def parse(self) -> List[ParsedSource]:
        return self._parser()

    @classmethod
    def generate_literal_model(  # noqa: C901
        cls,
        builder: TemplateHelper,
        parsed_source: ParsedSource,
        seed_model_type: Type[TModel],
        mappable_references: Optional[List[MappableReferenceField]] = None,
        class_name: Optional[str] = None,
        class_name_hints: Optional[List[str]] = None,
        require_all_fields_mapped: bool = False,
    ) -> LiteralModelBlueprint:
        """Generates a LiteralModelBlueprint with literal fields from a ParsedSource object.

        Args:
            builder (TemplateHelper): An interface to generate literal code.
            parsed_source (ParsedSource): A parsed source object containing data, typically represented
                as a dictionary of field names to field values.
            seed_model_type (Type[TModel]): The seed model type from which all generated literal classes
                will inherit.
            mappable_references (Optional[List[MappableReferenceField]], optional): A list of optional
                mappable reference fields used during the generation process. Defaults to None.
            class_name (Optional[str], optional): The name to assign to the literal class. If None,
                a name will be inferred using class_name_hints. Defaults to None.
            class_name_hints (Optional[List[str]], optional): Hints for inferring the class name if
                class_name is not provided. Defaults to None.
            require_all_fields_mapped (bool, optional): If True, raises a ValueError if any seed model
                fields are not mapped in the parsed source or mappable references. Defaults to False.

        Raises:
            ValueError: If require_all_fields_mapped is True and not all fields from the seed model are
                mapped.

        Returns:
            LiteralModelBlueprint: A blueprint containing the generated literal class and relevant
                metadata.
        """

        if class_name_hints is None:
            _class_name_hints = []
        else:
            _class_name_hints = class_name_hints.copy()

        _hint: Optional[str] = None
        # Solve for the class name
        while class_name is None and len(_class_name_hints) > 0:
            _hint = _class_name_hints.pop(0)
            class_name = parsed_source.get(_hint, None)
        if class_name is None:
            _hint = None
            raise ValueError("No class name provided and hint was found in the source data")
        class_blueprint = LiteralModelBlueprint(class_name)

        # Get all fields that exist in the seed pydantic model
        parent_model_fields = {
            field_name: field_info.annotation.__name__
            for field_name, field_info in seed_model_type.model_fields.items()
            if field_info.annotation is not None  # This should be safe as all types should be annotated by pydantic
        }

        # If require_all_fields_mapped is True, we will raise an error if
        # a field in the parent model is not found in the source data
        # or in on the the MappableReferenceField objects
        if require_all_fields_mapped:
            for field_name in parent_model_fields.keys():
                if mappable_references is not None:
                    mappable_fields = [mappable.parsed_source_keys for mappable in mappable_references]
                    if field_name not in mappable_fields:
                        raise ValueError(f"Field {field_name} not found in mappable fields")
                if field_name not in parsed_source.keys():
                    raise ValueError(f"Field {field_name} not found in source data")

                # Check if the seed class has the mappable field
                _mappable_references = mappable_references if mappable_references is not None else []
                for mappable in _mappable_references:
                    if not mappable.has_mappable_field(seed_model_type):
                        raise ValueError(f"Mappable field {mappable.field_name} not found in seed model")

        # Generate the class header
        class_blueprint.code_builder += builder.indent(
            builder.class_header(class_name=class_blueprint.sanitized_class_name, parent_name=seed_model_type.__name__),
            0,
        )

        # Populate the value-based fields
        for field_name in parent_model_fields.keys():
            _generated = False

            # 1) Mappable fields take priority over keys in csv
            _this_mappable = cls._try_get_mappable_reference_field(field_name, mappable_references)
            if _this_mappable is not None and not _generated:
                param = _this_mappable(parsed_source)
                param = helpers.unindent(param)
                _generated = True

            # 2) if 1) fails, we try to get the value from the source data
            if field_name in parsed_source.keys() and not _generated:
                param = parsed_source[field_name]
                if parent_model_fields[field_name] == "str":
                    param = f'"{param}"'
                _generated = True

            # 3) throw if strict and 1) and 2) fail
            if not _generated and require_all_fields_mapped:
                raise ValueError(f"Field {field_name} could not be generated")

            if _generated:
                class_blueprint.code_builder += builder.indent(builder.literal_field(name=field_name, value=param), 1)

        return class_blueprint

    @staticmethod
    def _try_get_mappable_reference_field(
        field_name: str, mappable_references: Optional[List[MappableReferenceField]]
    ) -> Optional[MappableReferenceField]:
        if mappable_references is None:
            return None
        for mappable in mappable_references:
            if mappable.field_name == field_name:
                return mappable
        return None

    @staticmethod
    def generate_enum_like_class(
        builder: TemplateHelper,
        class_name: str,
        discriminator: str,
        seed_model_type: type[TModel] | str,
        literal_model_blueprints: List[LiteralModelBlueprint],
        render_abbreviation_map: bool = True,
    ) -> str:
        """Generates code for an enum-like class containing instances of literal model classes.

        Args:
            builder (TemplateHelper): An interface responsible for generating literal code.
            class_name (str): The name of the class to be generated. Assumed to have been validated previously.
            discriminator (str): The field used as the discriminator in the union of all literal model types.
            seed_model_type (type[TModel] | str): The common seed model type (or its name) that all literal models inherit from.
            literal_model_blueprints (List[LiteralModelBlueprint]): The blueprints for all literal models to be included as
                values in the enum-like class.
            render_abbreviation_map (bool, optional): If True, renders the abbreviation map method as part of the class.
                Defaults to True.

        Returns:
            str: The generated code for the enum-like class as a string.
        """

        seed_model_name = seed_model_type if isinstance(seed_model_type, str) else seed_model_type.__name__
        string_builder = ""
        string_builder += builder.indent(builder.class_header(class_name=class_name), 0)

        for class_blueprint in literal_model_blueprints:
            string_builder += builder.indent(
                builder.model_enum_entry(
                    key=helpers.create_enum_key_from_class_name(class_blueprint.class_name),
                    value=class_blueprint.sanitized_class_name,
                ),
                1,
            )

        string_builder += builder.indent(builder.type_all_from_subclasses(parent_name=seed_model_name), 1)
        string_builder += builder.indent(
            builder.type_one_of(parent_name=seed_model_name, discriminator=discriminator), 1
        )
        if render_abbreviation_map:
            string_builder += builder.indent(builder.abbreviation_map(), 1)

        return string_builder
