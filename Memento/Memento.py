"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config

from .user import user_index
from .family import family_index, add_new_memory


class State(rx.State):
    """The app state."""

    ...


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Memento", 
                size="9",
            ),
            rx.text(
                "Stay connected with your family and cherish the memories of your loved ones!",
                size="5",
            ),
            spacing="5",
            justify="center",
            min_height="40vh",
        ),
        rx.hstack(
            rx.button(
                "User",
                color_scheme="grass",
                on_click=rx.redirect(
                    "/user"
                ),
                size="4",
            ),
            rx.button(
                "Family",
                color_scheme="grass",
                on_click=rx.redirect(
                    "/family"
                ),
                size="4",
            ),
        ),
    )


style = {
    "background_color": "#F5E0C3",
}

app = rx.App(
    style=style,
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="full",
    )
)


app.add_page(index)
app.add_page(user_index, route="/user")
app.add_page(family_index, route="/family")
app.add_page(add_new_memory, route="/family/new-memory")
