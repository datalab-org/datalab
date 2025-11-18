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

        return config


class HasUIHints(BaseModel):
    ui_layout: ClassVar[list[list[str]]] = []

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {}

    ui_virtual_fields: ClassVar[dict[str, dict[str, Any]]] = {}

    @classmethod
    def get_ui_schema(cls) -> dict[str, Any]:
        base_schema = cls.model_json_schema(by_alias=False)
        properties = base_schema.get("properties", {})
        defs = base_schema.get("$defs", {})

        for row in cls.ui_layout:
            for field_name in row:
                if field_name not in properties and field_name not in cls.ui_virtual_fields:
                    raise ValueError(
                        f"Field '{field_name}' in ui_layout does not exist in properties or ui_virtual_fields"
                    )

        if hasattr(cls, "ui_field_titles"):
            for field_name, custom_title in cls.ui_field_titles.items():
                if field_name in base_schema.get("properties", {}):
                    base_schema["properties"][field_name]["title"] = custom_title

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
            elif field_name in cls.ui_virtual_fields:
                virtual_field_info = cls.ui_virtual_fields[field_name]
                properties[field_name] = {
                    "type": "null",
                    "title": virtual_field_info.get("title", field_name),
                    "ui": config.to_dict(),
                }
                if "description" in virtual_field_info:
                    properties[field_name]["description"] = virtual_field_info["description"]

        for field_name, virtual_field_info in cls.ui_virtual_fields.items():
            if field_name not in properties:
                properties[field_name] = {
                    "type": "null",
                    "title": virtual_field_info.get("title", field_name),
                }
                if "description" in virtual_field_info:
                    properties[field_name]["description"] = virtual_field_info["description"]

        return {
            "properties": properties,
            "required": base_schema.get("required", []),
            "layout": cls.ui_layout,
            "title": base_schema.get("title"),
            "description": base_schema.get("description"),
        }
