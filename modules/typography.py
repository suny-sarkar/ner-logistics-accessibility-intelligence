"""
Typography Animation Utilities for NER Logistics Accessibility Intelligence.
Provides reusable functions to generate semantic HTML marked for GSAP/CSS cinematic text animation.
"""

def animated_heading(
    text: str, 
    level: int = 1, 
    anim_type: str = "chars", 
    className: str = "", 
    duration: float = 1.0, 
    stagger: float = 0.028, 
    delay: float = 0.0, 
    y: int = 35, 
    blur: int = 8, 
    once: bool = True
) -> str:
    """
    Renders an HTML heading tag (h1-h6) annotated with data attributes
    for cinematic typography animation.
    """
    tag = f"h{level}"
    class_attr = f' class="{className}"' if className else ""
    return (
        f'<{tag}{class_attr} data-anim-typography="true" '
        f'data-anim-type="{anim_type}" '
        f'data-anim-duration="{duration}" '
        f'data-anim-stagger="{stagger}" '
        f'data-anim-delay="{delay}" '
        f'data-anim-y="{y}" '
        f'data-anim-blur="{blur}" '
        f'data-anim-once="{"true" if once else "false"}">'
        f'{text}'
        f'</{tag}>'
    )

def animated_text(
    text: str, 
    tag: str = "span", 
    anim_type: str = "words", 
    className: str = "", 
    duration: float = 0.8, 
    stagger: float = 0.02, 
    delay: float = 0.0, 
    y: int = 20, 
    blur: int = 6, 
    once: bool = True
) -> str:
    """
    Renders an inline or block text tag (span, div, etc.) annotated for typography animation.
    """
    class_attr = f' class="{className}"' if className else ""
    return (
        f'<{tag}{class_attr} data-anim-typography="true" '
        f'data-anim-type="{anim_type}" '
        f'data-anim-duration="{duration}" '
        f'data-anim-stagger="{stagger}" '
        f'data-anim-delay="{delay}" '
        f'data-anim-y="{y}" '
        f'data-anim-blur="{blur}" '
        f'data-anim-once="{"true" if once else "false"}">'
        f'{text}'
        f'</{tag}>'
    )

def animated_paragraph(
    text: str, 
    className: str = "", 
    anim_type: str = "words", 
    duration: float = 0.75, 
    stagger: float = 0.012, 
    delay: float = 0.4, 
    y: int = 18, 
    blur: int = 4, 
    once: bool = True
) -> str:
    """
    Renders an HTML paragraph tag (<p>) annotated for word or line typography animation.
    """
    class_attr = f' class="{className}"' if className else ""
    return (
        f'<p{class_attr} data-anim-typography="true" '
        f'data-anim-type="{anim_type}" '
        f'data-anim-duration="{duration}" '
        f'data-anim-stagger="{stagger}" '
        f'data-anim-delay="{delay}" '
        f'data-anim-y="{y}" '
        f'data-anim-blur="{blur}" '
        f'data-anim-once="{"true" if once else "false"}">'
        f'{text}'
        f'</p>'
    )
