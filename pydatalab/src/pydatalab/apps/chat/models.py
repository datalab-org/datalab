from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel, ParrotFakeChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class ModelCard(BaseModel):
    name: str
    context_window: int
    input_cost_usd_per_MTok: float
    output_cost_usd_per_MTok: float
    chat_client: type[BaseChatModel] | None = Field(exclude=True)


__all__ = ("AVAILABLE_MODELS", "ModelCard")

_AVAILABLE_MODELS = [
    {
        "name": "langchain-debug",
        "context_window": 200_000_000,
        "input_cost_usd_per_MTok": 0.0,
        "output_cost_usd_per_MTok": 0.0,
        "chat_client": ParrotFakeChatModel,
    },
    {
        "name": "claude-3-5-sonnet-20241022",
        "context_window": 200_000,
        "input_cost_usd_per_MTok": 3.00,
        "output_cost_usd_per_MTok": 15.00,
        "chat_client": ChatAnthropic,
    },
    {
        "name": "claude-3-haiku-20241022",
        "context_window": 200_000,
        "input_cost_usd_per_MTok": 1.00,
        "output_cost_usd_per_MTok": 5.00,
        "chat_client": ChatAnthropic,
    },
    {
        "name": "claude-3-haiku-20240307",
        "context_window": 200_000,
        "input_cost_usd_per_MTok": 0.25,
        "output_cost_usd_per_MTok": 1.25,
        "chat_client": ChatAnthropic,
    },
    {
        "name": "claude-3-opus-20240229",
        "context_window": 200000,
        "input_cost_usd_per_MTok": 15.00,
        "output_cost_usd_per_MTok": 75.00,
        "chat_client": ChatAnthropic,
    },
    {
        "name": "gpt-4o",
        "context_window": 128000,
        "input_cost_usd_per_MTok": 5.00,
        "output_cost_usd_per_MTok": 15.00,
        "chat_client": ChatOpenAI,
    },
    {
        "name": "gpt-4o-mini",
        "context_window": 128_000,
        "input_cost_usd_per_MTok": 0.15,
        "output_cost_usd_per_MTok": 0.60,
        "chat_client": ChatOpenAI,
    },
    {
        "name": "gpt-4",
        "context_window": 8192,
        "input_cost_usd_per_MTok": 30.00,
        "output_cost_usd_per_MTok": 60.00,
        "chat_client": ChatOpenAI,
    },
    {
        "name": "gpt-4-turbo",
        "context_window": 128000,
        "input_cost_usd_per_MTok": 10.00,
        "output_cost_usd_per_MTok": 30.00,
        "chat_client": ChatOpenAI,
    },
]

AVAILABLE_MODELS: dict[str, ModelCard] = {
    model["name"]: ModelCard(**model) for model in _AVAILABLE_MODELS
}
