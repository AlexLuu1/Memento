"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config

from .user import user_index
from .family import family_index, add_new_memory

from .components import *


class State(rx.State):
    """The app state."""

    ...

def create_custom_heading(
    heading_type, font_size, margin_bottom, heading_text
):
    """Create a custom heading with specified font weight, margin, font size, and line height."""
    return rx.heading(
        heading_text,
        font_weight="600",
        margin_bottom=margin_bottom,
        font_size=font_size,
        line_height="1.75rem",
        as_=heading_type,
    )


def create_centered_heading(heading_text, color):
    """Create a centered heading with specific styling for section titles."""
    return rx.heading(
        heading_text,
        font_weight="600",
        margin_bottom="2rem",
        font_size="1.875rem",
        line_height="2.25rem",
        text_align="center",
        as_="h2",
        color=color
    )


def create_icon(alt_text, icon_tag):
    """Create an icon with specified dimensions and margins."""
    return rx.icon(
        alt=alt_text,
        tag=icon_tag,
        height="4rem",
        margin_bottom="1rem",
        margin_left="auto",
        margin_right="auto",
        width="4rem",
    )


def create_gray_text(text_content):
    """Create a text element with a specific gray color."""
    return rx.text(text_content, color="#4b5563")


def create_feature_box(
    icon_alt, icon_tag, title, description
):
    """Create a feature box with an icon, title, and description."""
    return rx.box(
        create_icon(alt_text=icon_alt, icon_tag=icon_tag),
        create_custom_heading(
            heading_type="h3",
            font_size="1.25rem",
            margin_bottom="0.5rem",
            heading_text=title,
        ),
        create_gray_text(text_content=description),
        text_align="center",
    )


def create_description_text(description):
    """Create a description text with specific margin and color."""
    return rx.text(
        description, margin_bottom="1rem", color="#4B5563"
    )


def create_learn_more_link():
    """Create a 'Learn More' link with hover effects."""
    return rx.el.a(
        "Learn More",
        href="#",
        font_weight="600",
        _hover={"color": "#74452f"},
        color="#74452f",
    )


def create_feature_card(title, description):
    """Create a feature card with a title, description, and 'Learn More' link."""
    return rx.box(
        create_custom_heading(
            heading_type="h3",
            font_size="1.25rem",
            margin_bottom="1rem",
            heading_text=title,
        ),
        create_description_text(description=description),
        create_learn_more_link(),
        background_color="#f9fafb",
        padding="1.5rem",
        border_radius="0.5rem",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    )


def create_social_icon(alt_text, icon_tag):
    """Create a social media icon with specified dimensions."""
    return rx.icon(
        alt=alt_text,
        tag=icon_tag,
        height="1.5rem",
        width="1.5rem",
    )


def create_social_link(icon_alt, icon_tag):
    """Create a social media link with an icon and hover effects."""
    return rx.el.a(
        create_social_icon(
            alt_text=icon_alt, icon_tag=icon_tag
        ),
        href="#",
        _hover={"color": "#D1D5DB"},
    )


# def create_header():
#     """Create the main header with logo and navigation links."""
#     return rx.flex(
#         rx.flex(
#             rx.image(
#                 src="/logo.png",
#                 alt="logo",
#                 height="4.5rem",
#                 margin_right="0.75rem",
#                 width="4.5rem",
#             ),
#             rx.text.span(
#                 "Memento",
#                 font_weight="600",
#                 color="#ffffff",
#                 font_size="2rem",
#                 line_height="1.75rem",
#             ),
#             display="flex",
#             align_items="center",
#         ),
#         rx.flex(
#             create_navigation_link(link_text="Home", path="/"),
#             create_navigation_link(link_text="User", path="/user"),
#             create_navigation_link(link_text="Family", path="/family"),
#             create_navigation_link(link_text="About", path="/"),
#             display="flex",
#             align_items="center",
#         ),
#         width="100%",
#         style=rx.breakpoints(
#             {
#                 "640px": {"max-width": "640px"},
#                 "768px": {"max-width": "768px"},
#                 "1024px": {"max-width": "1024px"},
#                 "1280px": {"max-width": "1280px"},
#                 "1536px": {"max-width": "1536px"},
#             }
#         ),
#         display="flex",
#         align_items="center",
#         justify_content="space-between",
#         margin_left="auto",
#         margin_right="auto",
#         padding_left="1.5rem",
#         padding_right="1.5rem",
#         padding_top="0.75rem",
#         padding_bottom="0.75rem",
#     )


def create_get_started_button():
    """Create a 'Get Started' button with hover effects."""
    return rx.el.a(
        "Get Started",
        href="/family/new-memory",
        background_color="#74452f",
        transition_duration="300ms",
        font_weight="600",
        _hover={"background-color": "#DBEAFE"},
        padding_left="2rem",
        padding_right="2rem",
        padding_top="0.75rem",
        padding_bottom="0.75rem",
        border_radius="9999px",
        color="#ffffff",
        transition_property="background-color, border-color, color, fill, stroke, opacity, box-shadow, transform",
        transition_timing_function="cubic-bezier(0.4, 0, 0.2, 1)",
    )


def create_hero_text_section():
    """Create the hero section text content with heading, description, and button."""
    return rx.box(
        rx.heading(
            "Capture Your Family Moments",
            font_weight="700",
            margin_bottom="1rem",
            font_size=rx.breakpoints(
                {"0px": "2.25rem", "768px": "3rem"}
            ),
            line_height=rx.breakpoints(
                {"0px": "2.5rem", "768px": "1"}
            ),
            as_="h1",
        ),
        rx.text(
            "Celebrate, connect, and preserve family moments with Memento.",
            margin_bottom="1.5rem",
            font_size="1.25rem",
            line_height="1.75rem",
        ),
        create_get_started_button(),
        margin_bottom=rx.breakpoints(
            {"0px": "2rem", "768px": "0"}
        ),
        # Set text width to 50% for medium+ screens
        width=rx.breakpoints({"768px": "50%"}),
    )


def create_hero_section():
    """Create the complete hero section with text and image."""
    return rx.flex(
        create_hero_text_section(),  # Left side: Hero text
        rx.box(
            rx.image(
                src="https://reflex-hosting-dev-flexgen.s3.us-west-2.amazonaws.com/replicate/bLysAF0Me6SEYqfzSLXl3eX0pcNfnlkAxWdKoB5W4XOGcGiOB/out-0.webp",
                alt="Happy family enjoying outdoor activities",
                border_radius="0.5rem",
                box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                max_width="100%",  # Ensures the image is responsive
            ),
            # Reduce image width to 25% for medium+ screens
            width=rx.breakpoints({"768px": "48%"}),
        ),
        width="100%",  # Full width of the container
        style=rx.breakpoints(
            {
                # Vertical layout on small screens
                "0px": {"flex_direction": "column"},
                # Horizontal layout on medium+ screens
                "768px": {"flex_direction": "row"}
            }
        ),
        align_items="center",  # Center vertically
        justify_content="space-between",  # Space between text and image
        padding="2.5rem",
        padding_left="10rem",
        padding_right="10rem",
    )


def create_how_it_works_section():
    """Create the 'How It Works' section with feature boxes."""
    return rx.box(
        create_centered_heading(
            heading_text="How It Works", color="#000000"
        ),
        rx.box(
            create_feature_box(
                icon_alt="Camera icon",
                icon_tag="camera",
                title="Capture Moments",
                description="Take photos and videos of your family's special moments.",
            ),
            create_feature_box(
                icon_alt="Share icon",
                icon_tag="share-2",
                title="Share Instantly",
                description="Share your memories with family members in real-time.",
            ),
            create_feature_box(
                icon_alt="Heart icon",
                icon_tag="heart",
                title="Relive Memories",
                description="Revisit and cherish your family's precious moments anytime.",
            ),
            gap="2rem",
            display="grid",
            grid_template_columns=rx.breakpoints(
                {
                    "0px": "repeat(1, minmax(0, 1fr))",
                    "768px": "repeat(3, minmax(0, 1fr))",
                }
            ),
        ),
        width="100%",
        style=rx.breakpoints(
            {
                "640px": {"max-width": "640px"},
                "768px": {"max-width": "768px"},
                "1024px": {"max-width": "1024px"},
                "1280px": {"max-width": "1280px"},
                "1536px": {"max-width": "1536px"},
            }
        ),
        margin_left="auto",
        margin_right="auto",
        padding_left="1.5rem",
        padding_right="1.5rem",
    )


def create_features_section():
    """Create the 'Features' section with feature cards."""
    return rx.box(
        create_centered_heading(heading_text="Features", color="#ffffff"),
        rx.box(
            create_feature_card(
                title="User Dashboard",
                description="Manage your profile, settings, and personal memories in one place.",
            ),
            create_feature_card(
                title="Family Album",
                description="Create and share albums with your family members, organizing memories by events or dates.",
            ),
            create_feature_card(
                title="Shared Calendar",
                description="Keep track of family events, birthdays, and important dates in a collaborative calendar.",
            ),
            create_feature_card(
                title="Family Chat",
                description="Stay connected with your loved ones through our integrated family chat feature.",
            ),
            gap="2rem",
            display="grid",
            grid_template_columns=rx.breakpoints(
                {
                    "0px": "repeat(1, minmax(0, 1fr))",
                    "768px": "repeat(2, minmax(0, 1fr))",
                }
            ),
        ),
        width="100%",
        style=rx.breakpoints(
            {
                "640px": {"max-width": "640px"},
                "768px": {"max-width": "768px"},
                "1024px": {"max-width": "1024px"},
                "1280px": {"max-width": "1280px"},
                "1536px": {"max-width": "1536px"},
            }
        ),
        margin_left="auto",
        margin_right="auto",
        padding_left="1.5rem",
        padding_right="1.5rem",
    )


def create_main_content():
    """Create the main content including hero, how it works, and features sections."""
    return rx.box(
        rx.box(
            create_hero_section(),
            background_color="#F5E0C3",
            color="#000000",
        ),
        rx.box(
            create_how_it_works_section(),
            padding_top="4rem",
            padding_bottom="4rem",
        ),
        rx.box(
            create_features_section(),
            background_color="#ae7b58",
            padding_top="4rem",
            padding_bottom="4rem",
        ),
    )

def create_page_layout():
    """Create the overall page layout including header, main content, and footer."""
    return rx.box(
        rx.box(
            create_header(),
            background_color="#74452f",
            box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        ),
        create_main_content(),
        rx.box(
            create_footer(),
            background_color="#ffffff",
            padding_top="2rem",
            padding_bottom="2rem",
            color="#1F2937",
        ),
        background_color="#F3F4F6",
        font_family='system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
    )


def create_app():
    """Create the main application structure with necessary styles and layout."""
    return rx.fragment(
        rx.el.link(
            href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
            rel="stylesheet",
        ),
        rx.el.style(
            """
        @font-face {
            font-family: 'LucideIcons';
            src: url(https://unpkg.com/lucide-static@latest/font/Lucide.ttf) format('truetype');
        }
    """
        ),
        create_page_layout(),
    )


def index() -> rx.Component:
    """The main page of the application."""
    return rx.fragment(
        rx.el.link(
            href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
            rel="stylesheet",
        ),
        rx.el.style(
            """
            @font-face {
                font-family: 'LucideIcons';
                src: url(https://unpkg.com/lucide-static@latest/font/Lucide.ttf) format('truetype');
            }
            """
        ),
        create_page_layout(),
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="full",
        global_styles={
            "body": {
                "background_color": "#F3F4F6",
                "font_family": 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
                "color": "#333333",
            }
        }
    )
)

app.add_page(index)
app.add_page(user_index, route="/user")
