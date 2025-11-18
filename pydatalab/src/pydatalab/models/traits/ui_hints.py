from typing import Any, ClassVar

from pydantic import BaseModel


class UIFieldConfig:
    def __init__(
        self,
        component: str,
        width: str = "col",
        readonly: bool = False,
        hidden: bool = False,
        hide_label: bool = False,
        has_builtin_label: bool = False,
        component_props: dict[str, Any] | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        """
        Configure UI rendering for a field.

        Args:
            component: The Vue component name to use for rendering
            width: Bootstrap grid classes for field width
            readonly: Whether the field is read-only
            hidden: Whether the field should be hidden
            hide_label: Whether to hide the field label
            has_builtin_label: Whether the component renders its own label
            component_props: Additional props to pass to the component
        """
        self.component = component
        self.width = width
        self.readonly = readonly
        self.hidden = hidden
        self.hide_label = hide_label
        self.has_builtin_label = has_builtin_label
        self.component_props = component_props
        self.title = title
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "component": self.component,
            "width": self.width,
        }

        if self.readonly:
            config["readonly"] = True
        if self.hidden:
            config["hidden"] = True
        if self.hide_label:
            config["hide_label"] = True
        if self.has_builtin_label:
            config["has_builtin_label"] = True
        if self.component_props:
            config["component_props"] = self.component_props
        if self.title:
            config["title"] = self.title
        if self.description:
            config["description"] = self.description

        return config


class HasUIHints(BaseModel):
    ui_layout: ClassVar[list[list[str]]] = []

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {}

    @classmethod
    def get_ui_schema(cls) -> dict[str, Any]:
        base_schema = cls.model_json_schema(by_alias=False)
        properties = base_schema.get("properties", {})
        defs = base_schema.get("$defs", {})

        for row in cls.ui_layout:
            for field_name in row:
                if field_name not in properties and field_name not in cls.ui_field_config:
                    raise ValueError(
                        f"Field '{field_name}' in ui_layout does not exist in properties or ui_field_config"
                    )

        for field_name, field_schema in properties.items():
            if "anyOf" in field_schema:
                for option in field_schema["anyOf"]:
                    if "$ref" in option:
                        ref_path = option["$ref"].split("/")[-1]
                        if ref_path in defs:
                            ref_definition = defs[ref_path]
                            if "enum" in ref_definition:
                                field_schema["enum"] = ref_definition["enum"]
                                if "type" in ref_definition and "type" not in field_schema:
                                    field_schema["type"] = ref_definition["type"]

        for field_name, config in cls.ui_field_config.items():
            if field_name in properties:
                properties[field_name]["ui"] = config.to_dict()
                if config.title:
                    properties[field_name]["title"] = config.title
                if config.description:
                    properties[field_name]["description"] = config.description
            else:
                properties[field_name] = {
                    "type": "null",
                    "title": config.title or field_name,
                    "ui": config.to_dict(),
                }
                if config.description:
                    properties[field_name]["description"] = config.description

        return {
            "properties": properties,
            "required": base_schema.get("required", []),
            "layout": cls.ui_layout,
            "title": base_schema.get("title"),
            "description": base_schema.get("description"),
        }
