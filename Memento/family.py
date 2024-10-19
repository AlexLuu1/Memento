import reflex as rx
from rxconfig import config
from datetime import datetime

from PIL import Image
import requests


class FamilyState(rx.State):
    temp_image = Image.open(requests.get("https://www.parents.com/thmb/--pZafKsgGSb8NrJVrV7lqJId9g=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/BirthdayParty-GettyImages-1600792233-c2a961509556414f9f41b92b8471a551.jpg", stream=True).raw)

    posts: list[dict] = [
        {"id": 1, "author": "Mom", "content": "Just baked cookies!", "timestamp": "2024-10-18 14:30"},
        {"id": 2, "author": "Dad", "content": "Family picnic this weekend?", "timestamp": "2024-10-18 15:45"},
    ]
    events: list[dict] = [
        {"id": 1, "title": "Grandma's Birthday", "date": "2024-10-25"},
        {"id": 2, "title": "Family Reunion", "date": "2024-11-15"},
    ]
    new_post: str = ""
    new_memory_description: str = ""
    current_view: str = "memories"

    def add_post(self):
        if self.new_post.strip():
            self.posts.append({
                "id": len(self.posts) + 1,
                "author": "You",
                "content": self.new_post,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            self.new_post = ""

    def add_memory(self):
        if self.new_memory_description.strip():
            # In a real app, you'd handle image upload here
            self.posts.insert(0, {
                "id": len(self.posts) + 1,
                "author": "You",
                "content": self.new_memory_description,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": self.temp_image
            })
            self.new_memory_description = ""

    def set_view(self, view: str):
        self.current_view = view


def family_index():
    return rx.container(
        rx.spacer(),
        rx.vstack(
            rx.heading("Family", size="9"),
            rx.text(
                "Add new memories here!",
                size="5",
            ),
            rx.button(
                "Add New Memory",
                color_scheme="grass",
                on_click=rx.redirect(
                    "/family/new-memory"
                ),
                size="4",
            ),
            rx.spacer(),
            spacing="5",
            justify="center",
            min_height="15vh",
        ),
        rx.grid(
            rx.foreach(
                rx.Var.range(5),
                lambda i: rx.card(
                    rx.hstack(
                        rx.image(
                            src=FamilyState.temp_image,
                            width="200px",
                            height="auto",
                        ),
                        rx.text(
                            "MEMORY DESCRIPTION"
                        ),
                    ),
                ),
            ),
            columns="1",
            spacing="4",
            width="100%",
        ),
        rx.spacer(),
    )



class NewMemory(rx.State):
    date = ""
    description = ""

    form_data: dict = {}

    def handle_submit(self, form_data: dict):
        date = form_data["date"]
        description = form_data["description"]

        return rx.redirect(
            "/family"
        )


def add_new_memory():
    return rx.container(
        rx.spacer(),
        rx.form(
            rx.vstack(
                rx.input(
                    name="date",
                    placeholder="Enter text...",
                    type="text",
                    required=True,
                ),
                rx.input(
                    name="description",
                    placeholder="Enter text...",
                    type="text",
                    required=False,
                ),
                # rx.upload(
                #     rx.vstack(
                #         rx.button(
                #             "Select File",
                #             color="black",
                #             bg="white",
                #             border=f"1px solid black",
                #         ),
                #         rx.text(
                #             "Drag and drop files here or click to select files"
                #         ),
                #     ),
                #     id="upload1",
                #     border=f"1px dotted black",
                #     padding="5em",
                # ),
                rx.button("Submit", type="submit"),
                width="100%",
            ),
            on_submit=NewMemory.handle_submit,
            reset_on_submit=True,
        ),
        rx.spacer(),
    )