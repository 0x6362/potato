from potato.solo_mode.instance_view import (
    DisplayError,
    PlainTextDisplay,
    StructuredDisplay,
    build_solo_instance_view,
)


def test_uses_plain_text_when_instance_display_is_not_configured():
    view = build_solo_instance_view(
        instance_id="item-1",
        displayed_text="legacy text",
        instance_data={"text": "legacy text"},
        app_config={},
    )

    assert view.id == "item-1"
    assert isinstance(view.display, PlainTextDisplay)
    assert view.display.text == "legacy text"


def test_renders_configured_dialogue_and_escapes_turn_content():
    config = {
        "instance_display": {
            "fields": [
                {
                    "key": "conversation",
                    "type": "dialogue",
                    "display_options": {
                        "alternating_shading": True,
                        "show_turn_numbers": True,
                    },
                }
            ]
        }
    }
    view = build_solo_instance_view(
        instance_id="item-2",
        displayed_text="unused scorer input",
        instance_data={
            "conversation": [
                {"speaker": "User", "text": "Hello"},
                {
                    "speaker": "Assistant",
                    "text": "First line\n<script>alert('x')</script>",
                },
                {"speaker": "User (target)", "text": "Thanks"},
            ]
        },
        app_config=config,
    )

    assert isinstance(view.display, StructuredDisplay)
    assert "dialogue-display-content" in view.display.html
    assert "User (target)" in view.display.html
    assert "&lt;script&gt;" in view.display.html
    assert "<script>" not in view.display.html


def test_models_missing_display_fields_as_an_error_value():
    view = build_solo_instance_view(
        instance_id="item-3",
        displayed_text="fallback text",
        instance_data={"text": "fallback text"},
        app_config={
            "instance_display": {
                "fields": [{"key": "conversation", "type": "dialogue"}]
            }
        },
    )

    assert isinstance(view.display, DisplayError)
    assert "conversation" in view.display.message
