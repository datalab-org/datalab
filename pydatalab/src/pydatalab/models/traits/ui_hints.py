from typing import Any, ClassVar

from pydantic import BaseModel


class UIFieldConfig:
    def __init__(
        self,
        component: str,
        width: str = "col",
        readonly: bool = False,
        hidden: bool = False,
    ):
        self.component = component
        self.width = width
        self.readonly = readonly
        self.hidden = hidden

    def to_dict(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "component": self.component,
            "width": self.width,
        }
        if self.readonly:
            config["readonly"] = True
        if self.hidden:
            config["hidden"] = True
        return config


class HasUIHints(BaseModel):
    ui_layout: ClassVar[list[list[str]]] = []

    ui_field_config: ClassVar[dict[str, UIFieldConfig]] = {}

    @classmethod
    def get_ui_schema(cls) -> dict[str, Any]:
        base_schema = cls.model_json_schema()
        properties = base_schema.get("properties", {})

        for field_name, config in cls.ui_field_config.items():
            if field_name in properties:
                properties[field_name]["ui"] = config.to_dict()

        return {
            "properties": properties,
            "required": base_schema.get("required", []),
            "layout": cls.ui_layout,
            "title": base_schema.get("title"),
            "description": base_schema.get("description"),
        }
