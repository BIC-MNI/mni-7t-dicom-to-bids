"""Validation models for the JSON5 dictionary, before references and files are resolved."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

NonEmptyString = Annotated[str, Field(min_length=1)]


class DictionaryConfigModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='forbid',
        regex_engine='python-re',
        allow_inf_nan=False,
    )


class CitationConfig(DictionaryConfigModel):
    text: NonEmptyString
    url: Annotated[str, Field(pattern=r'^https?://[^\s/]+(?:/[^\s]*)?\Z')]


class CreditConfig(DictionaryConfigModel):
    acknowledgement: NonEmptyString
    references: list[NonEmptyString | CitationConfig] = Field(default_factory=list[str | CitationConfig])


class DerivativeConfig(DictionaryConfigModel):
    name: Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9-]*\Z')]
    dataset_description: NonEmptyString = Field(alias='dataset-description')


class MappingConfig(DictionaryConfigModel):
    series: NonEmptyString
    datatype: Literal['anat', 'dwi', 'fmap', 'func']
    filename: Annotated[str, Field(pattern=r'^[A-Za-z0-9_-]+\Z')]
    merge_images: bool = Field(default=False, alias='merge-images')
    derivative: NonEmptyString | DerivativeConfig | None = None
    sidecar: dict[str, JsonValue] = Field(default_factory=dict[str, JsonValue])
    credit: CreditConfig | None = None


class DictionaryConfig(DictionaryConfigModel):
    ignored_series: list[NonEmptyString] = Field(alias='ignored-series')
    trim_series_suffixes: list[NonEmptyString] = Field(alias='trim-series-suffixes')
    mappings: list[MappingConfig]
    references: dict[NonEmptyString, CitationConfig] = Field(default_factory=dict)
    derivatives: dict[NonEmptyString, DerivativeConfig] = Field(default_factory=dict)


# Dataset descriptions are extensible BIDS metadata. Validate the fields the
# converter needs, while preserving every other field from the template.
class DatasetGeneratorConfig(DictionaryConfigModel):
    model_config = ConfigDict(extra='allow')

    name: NonEmptyString = Field(alias='Name')


class DatasetDescriptionConfig(DictionaryConfigModel):
    model_config = ConfigDict(extra='allow')

    dataset_type: Literal['derivative'] = Field(alias='DatasetType')
    generated_by: Annotated[list[DatasetGeneratorConfig], Field(min_length=1)] = Field(alias='GeneratedBy')
