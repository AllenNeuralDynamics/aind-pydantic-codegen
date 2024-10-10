# aind-pydantic-codegen
A library for automatic generation of pydantic models


## Instructions

> **Warning**: The library is still in development and may not work as expected. Please use it with caution.


1. Install the library using pip and github
```bash
pip install git+https://github.com/AllenNeuralDynamics/aind-pydantic-codegen@main
```

> **Note**: You can lock the version of the library by replacing `main` with the desired release/tag/branch/commit.

1. In python, generate code using the context manager. Eg.:

```python
from typing import Dict, List

import pydantic

from aind_pydantic_codegen.formatters import BlackFormatter, ISortFormatter
from aind_pydantic_codegen.generators import GeneratorContext, ModelGenerator
from aind_pydantic_codegen.validators import AstValidator


class SeedClassModel(pydantic.BaseModel):
    name: str
    value: str


data_source: List[Dict[str, str]] = [
    {"name": "Foo", "value": "I am Foo"},
    {"name": "Bar", "value": "I am Bar"},
]

model_generator = ModelGenerator(
    class_name="SeedClass",
    seed_model_type=SeedClassModel,
    discriminator="name",
    data_source_identifier="not_chat_gpt",
    parser=lambda: data_source,
    default_module_name="aind_pydantic_codegen.generators",
)

with GeneratorContext(code_validators=[AstValidator()], code_formatters=[BlackFormatter(), ISortFormatter()]) as ctx:
    ctx.add_generator(model_generator, "seed_class.py")
    ctx.write_all()
```