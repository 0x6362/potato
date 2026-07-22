"""Presentation model for instances rendered by the Solo Mode workflow."""

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Union

from potato.server_utils.instance_display import get_instance_display_renderer


@dataclass(frozen=True)
class StructuredDisplay:
    """Trusted HTML produced by Potato's configured instance renderer."""

    kind: ClassVar[str] = "structured"
    html: str


@dataclass(frozen=True)
class PlainTextDisplay:
    """Legacy text shown when no structured display is configured."""

    kind: ClassVar[str] = "plain_text"
    text: str


@dataclass(frozen=True)
class DisplayError:
    """A visible rendering failure that preserves the annotation page."""

    kind: ClassVar[str] = "error"
    message: str


SoloDisplay = Union[StructuredDisplay, PlainTextDisplay, DisplayError]


@dataclass(frozen=True)
class SoloInstanceView:
    """The single display state presented for a Solo Mode instance."""

    id: str
    data: Dict[str, Any]
    display: SoloDisplay


def build_solo_instance_view(
    instance_id: str,
    displayed_text: str,
    instance_data: Dict[str, Any],
    app_config: Dict[str, Any],
) -> SoloInstanceView:
    """Select exactly one structured, plain-text, or error display state."""
    if not app_config.get("instance_display"):
        display = PlainTextDisplay(displayed_text)
        return SoloInstanceView(instance_id, instance_data, display)

    try:
        variables = get_instance_display_renderer(app_config).get_template_variables(
            instance_data
        )
    except Exception as error:
        message = str(error) or error.__class__.__name__
        return SoloInstanceView(instance_id, instance_data, DisplayError(message))

    if variables.get("display_error"):
        display = DisplayError(str(variables["display_error"]))
    elif variables.get("display_html"):
        display = StructuredDisplay(str(variables["display_html"]))
    else:
        display = DisplayError("Configured instance display produced no content")

    return SoloInstanceView(instance_id, instance_data, display)
