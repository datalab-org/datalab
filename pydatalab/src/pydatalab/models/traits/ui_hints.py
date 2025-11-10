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
    ):
        self.component = component
        self.width = width
        self.readonly = readonly
        self.hidden = hidden
        self.hide_label = hide_label

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
        return config


class HasUIHints(BaseModel):
    ui_layout: ClassVar[list[list[str]]] = []

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {}

    ui_virtual_fields: ClassVar[dict[str, dict[str, Any]]] = {}

    @classmethod
    def get_ui_schema(cls) -> dict[str, Any]:
        base_schema = cls.model_json_schema()
        properties = base_schema.get("properties", {})

        for field_name, config in cls.ui_field_config.items():
            if field_name in properties:
                properties[field_name]["ui"] = config.to_dict()
            elif field_name in cls.ui_virtual_fields:
                properties[field_name] = {
                    "type": "null",
                    "title": cls.ui_virtual_fields[field_name].get("title", field_name),
                    "ui": config.to_dict(),
                }

        return {
            "properties": properties,
            "required": base_schema.get("required", []),
            "layout": cls.ui_layout,
            "title": base_schema.get("title"),
            "description": base_schema.get("description"),
        }
