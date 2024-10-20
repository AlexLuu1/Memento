import reflex as rx
from rxconfig import config
from datetime import datetime

from PIL import Image
import io
import requests
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
import uuid
from typing import List

from .components import *

# Add the create_themed_page function
def create_custom_heading(heading_type, font_size, margin_bottom, heading_text):
    return rx.heading(
        heading_text,
        font_weight="600",
        margin_bottom=margin_bottom,
        font_size=font_size,
        line_height="1.75rem",
        as_=heading_type,
    )

def create_themed_page(content):
    """Wrap the given content with header and footer, applying the theme."""
    return rx.box(
        create_header(),
        content,
        create_footer(),
        background_color="#F3F4F6",  # Consistent background
        font_family='system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
    )

genai.configure(api_key='YOUR_API_KEY')
text_to_img_model = genai.GenerativeModel("gemini-1.5-flash")


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = 'models/embedding-001'
        title = "Custom query"
        return genai.embed_content(
            model=model,
            content=input,
            task_type="retrieval_document",
            title=title
        )["embedding"]


class FamilyState(rx.State):
    data: List[tuple[str, str]] = []

    def get_data(self):
        self.data = []
        collection = chromadb.HttpClient(
            host='localhost', port=8001
        ).get_or_create_collection(
            name="vectordb",
            embedding_function=GeminiEmbeddingFunction()
        )
        results = collection.get()

        documents = results["documents"]
        metadatas = results["metadatas"]

        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            print(doc)
            date, description, image_summary = doc.split('|', 2)
            self.data.append((description, metadata['filename'] + ".jpg"))
        print(self.data)


def single_render(single_data: tuple):
    return rx.box(
        rx.box(
            rx.image(
                src=rx.get_upload_url(single_data[1]),
                width="100%",
                height="auto",
                border_radius="0.5rem 0.5rem 0 0",
            ),
            rx.box(
                rx.text(single_data[0], padding="1rem"),
            ),
            overflow="hidden",
            box_shadow="0 4px 6px rgba(0, 0, 0, 0.1)",
            border_radius="0.5rem",
            background_color="#ffffff",
            width="85%",
        ),
        text_align="center",
        display="flex",
        flex_direction="column",
        align_items="center",
    )


@rx.page(on_load=FamilyState.get_data, route="/family")
def family_index():
    content = rx.box(
        rx.box(
            rx.heading(
                "Family Memories",
                font_size="2rem",
                font_weight="600",
                margin_bottom="1rem"
            ),
            rx.text(
                "Capture and relive your most cherished moments with your loved ones! Share anything ",
                font_size="1.25rem",
                margin_bottom="1rem",
            ),
            rx.el.a(
                "Add New Memory",
                href="/family/new-memory",
                background_color="#74452f",
                color="#ffffff",
                padding="0.75rem 1.5rem",
                border_radius="0.375rem",
                _hover={"background_color": "#5a3722"},
                margin_bottom="2rem",
                display="inline-block",
            ),
        ),
        rx.grid(
            rx.foreach(
                FamilyState.data,
                single_render
            ),
            template_columns=rx.breakpoints(
                {
                    "0px": "repeat(1, minmax(0, 1fr))",
                    "768px": "repeat(2, minmax(0, 1fr))",
                    "1024px": "repeat(3, minmax(0, 1fr))",
                }
            ),
            gap="2rem",
        ),
        width="100%",
        max_width="1280px",
        margin_left="auto",
        margin_right="auto",
        padding="2rem",
    )
    return create_themed_page(content)


class NewMemory(rx.State):
    date = ""
    description = ""
    generated_uuid = ""

    def handle_submit(self, form_data: dict):
        self.date = form_data["date"]
        self.description = form_data["description"]

        # Connect to ChromaDB
        collection = chromadb.HttpClient(
            host='localhost', port=8001
        ).get_or_create_collection(
            name="vectordb",
            embedding_function=GeminiEmbeddingFunction()
        )

        self.generated_uuid = str(uuid.uuid4())

        docs = f"{self.date}|{self.description}",  # TODO: add prompt engineering stuff

        collection.upsert(
            documents=docs,
            metadatas=[{"filename": self.generated_uuid}],
            ids=[self.generated_uuid],
        )

        old_data = collection.get(ids=[self.generated_uuid])
        print("1st function data", old_data)

        return rx.redirect("/family")

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of file(s)."""
        collection = chromadb.HttpClient(
            host='localhost', port=8001
        ).get_or_create_collection(
            name="vectordb",
            embedding_function=GeminiEmbeddingFunction()
        )

        for file in files:
            upload_data = await file.read()
            outfile = f"{rx.get_upload_dir()}/{self.generated_uuid}.jpg"

            print(outfile)

            # Save the image
            image = Image.open(io.BytesIO(upload_data))
            if image.mode != "RGB":
                image = image.convert("RGB")

            image.save(outfile, format="JPEG")

            # Get text from image with Gemini
            myfile = genai.upload_file(outfile, mime_type="image/jpeg")
            print(f"{myfile=}")

            result = text_to_img_model.generate_content(
                [myfile, "\n\n", "Please give me a description of this image as detailed as possible"]
            )
            print(f"{result.text=}")

            old_data = collection.get(ids=[self.generated_uuid])
            print("1st function old data", old_data)

            docs = f"{old_data['documents'][0]}|{result.text}",  # TODO: add prompt engineering stuff

            collection.upsert(
                documents=docs,
                metadatas=[{"filename": self.generated_uuid}],
                ids=[self.generated_uuid],
            )

            old_data = collection.get(ids=[self.generated_uuid])
            print("2nd function data", old_data)


@rx.page(route="/family/new-memory")
def add_new_memory():
    content = rx.box(
        rx.box(
            create_custom_heading(
                heading_type="h2",
                font_size="2rem",
                margin_bottom="1rem",
                heading_text="Add a New Memory",
            ),
            rx.form(
                rx.box(
                    rx.box(
                        rx.el.label("Date of Memory", font_weight="600"),
                        rx.input(
                            name="date",
                            type="date",
                            required=True,
                            width="100%",
                            padding="0.5rem",
                            border="1px solid #ccc",
                            border_radius="0.375rem",
                            margin_bottom="1rem",
                        ),
                    ),
                    rx.box(
                        rx.el.label("Description", font_weight="600"),
                        rx.text_area(
                            name="description",
                            placeholder="Enter description...",
                            required=True,
                            resize="vertical",
                            width="100%",
                            padding="0.5rem",
                            border="1px solid #ccc",
                            border_radius="0.375rem",
                            margin_bottom="1rem",
                        ),
                    ),
                    rx.box(
                        rx.el.label("Upload a Picture", font_weight="600"),
                        rx.upload(
                            rx.vstack(
                                rx.button(
                                    "Select File",
                                    background_color="#74452f",
                                    color="#ffffff",
                                    padding="0.5rem 1rem",
                                    border_radius="0.375rem",
                                    _hover={"background_color": "#5a3722"},
                                    type="button",
                                ),
                                rx.text(
                                    "Drag and drop files here or click to select files",
                                    font_size="0.875rem",
                                    color="#6B7280",
                                ),
                                rx.foreach(
                                    rx.selected_files("upload1"),
                                    lambda file: rx.text(file._js_expr, color="#4B5563")
                                ),
                            ),
                            id="upload1",
                            border="2px dashed #ccc",
                            padding="1rem",
                            border_radius="0.375rem",
                            margin_bottom="1rem",
                        ),
                    ),
                    rx.button(
                        "Submit",
                        type="submit",
                        background_color="#74452f",
                        color="#ffffff",
                        padding="0.75rem 1.5rem",
                        border_radius="0.375rem",
                        _hover={"background_color": "#5a3722"},
                    ),
                ),
                on_submit=[
                    NewMemory.handle_submit,
                    NewMemory.handle_upload(rx.upload_files(upload_id="upload1"))
                ],
                width="100%",
                max_width="600px",
                margin_left="auto",
                margin_right="auto",
                padding="1rem",
                background_color="#ffffff",
                border_radius="0.5rem",
                box_shadow="0 4px 6px rgba(0, 0, 0, 0.1)",
            ),
        ),
        width="100%",
        padding="2rem",
    )
    return create_themed_page(content)
