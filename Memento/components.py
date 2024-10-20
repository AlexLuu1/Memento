import reflex as rx


def create_navigation_link(link_text, path):
    """Create a navigation link with hover effects and specific padding."""
    return rx.el.a(
        link_text,
        href=path,
        font_size="1.25rem",
        _hover={"color": "#ffffff"},
        padding_left="0.75rem",
        padding_right="0.75rem",
        padding_top="0.5rem",
        padding_bottom="0.5rem",
        color="#ffffff",
    )


def create_header():
    """Create the main header with logo and navigation links."""
    return rx.box(  # Use box to ensure full width
        rx.flex(
            rx.flex(
                rx.image(
                    src="/logo.png",
                    alt="logo",
                    height="4.5rem",
                    margin_right="0.75rem",
                    width="4.5rem",
                ),
                rx.text.span(
                    "Memento",
                    font_weight="600",
                    color="#ffffff",
                    font_size="2rem",
                    line_height="1.75rem",
                ),
                display="flex",
                align_items="center",
            ),
            rx.flex(
                create_navigation_link(link_text="Home", path="/"),
                create_navigation_link(link_text="User", path="/user"),
                create_navigation_link(link_text="Family", path="/family"),
                create_navigation_link(link_text="About", path="/"),
                display="flex",
                align_items="center",
            ),
            width="100%",
            justify_content="space-between",
            align_items="center",
        ),
        width="100vw",  # Full viewport width
        padding_left="7rem",
        padding_right="7rem",
        padding_top="0.75rem",
        padding_bottom="0.75rem",
        background_color="#74452f",
    )

def create_footer():
    """Create the footer with simple content."""
    return rx.box(
        rx.text("© 2024 Memento. All rights reserved."),
        text_align="center",
        font_size="0.875rem",
        line_height="1.25rem",
        padding="1rem",
        border_top="1px solid #ccc",
        background_color="#ffffff",
    )

