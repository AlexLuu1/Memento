import reflex as rx
from rxconfig import config
from datetime import datetime
import os

from PIL import Image
import io
import requests
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
import uuid
from typing import List, TypedDict

from .components import * 



# Custom Heading Component
def create_custom_heading(
    heading_type: str,
    font_size: str,
    margin_bottom: str,
    heading_text: str
) -> rx.Component:
    return rx.heading(
        heading_text,
        font_weight="600",
        margin_bottom=margin_bottom,
        font_size=font_size,
        line_height="1.75rem",
        as_=heading_type,
    )


# Themed Page Wrapper
def create_themed_page(content: rx.Component) -> rx.Component:
    """Wrap the given content with header and footer, applying the theme."""
    return rx.box(
        create_header(),
        content,
        create_footer(),
        background_color="#F3F4F6",
        font_family=(
            'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
            '"Helvetica Neue", Arial, "Noto Sans", sans-serif'
        ),
    )


# Configure Google Generative AI
# Replace with your actual API key securely
# **Important**: Use environment variables in production
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
text_to_img_model = genai.GenerativeModel("gemini-1.5-flash")


# Custom Embedding Function for ChromaDB
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


# State Management for Family Memories
class FamilyState(rx.State):
    data: List[dict[str, str]] = []

    def get_data(self) -> None:
        self.data = []
        collection = chromadb.HttpClient(
            host='localhost', port=8001
        ).get_or_create_collection(
            name="vectordb",
            embedding_function=GeminiEmbeddingFunction()
        )
        results = collection.get()

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        for doc, metadata in zip(documents, metadatas):
            try:
                date_str, description, image_summary = doc.split('|', 2)
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_formatted = date_obj.strftime("%B %d, %Y")
                image_filename = f"{str(metadata['filename'])}.jpg"
                self.data.append({
                    "date": date_formatted,
                    "description": description,
                    "image_filename": image_filename
                })
            except ValueError as e:
                print(f"Error parsing document: {e}")
                continue

        # Sort the data by date in descending order (newest first)
        self.data.sort(key=lambda x: x["date"], reverse=True)
        print(self.data)


# Timeline Event Component
# Timeline Event Component
def TimelineEvent(event_data: dict[str, str]) -> rx.Component:
    date_formatted = event_data["date"]
    filename = event_data["image_filename"]

    # Generate the image URL and set a placeholder in case of error
    image_url = rx.get_upload_url(filename)
    placeholder_url = "/static/placeholder.jpg"

    return rx.box(
        rx.hstack(
            # Left side: Date (hidden on mobile)
            rx.box(
                rx.text(
                    date_formatted,
                    font_weight="600",
                    font_size="1rem",
                    color="#333",
                    text_align="right",
                ),
                width="175px",
                padding_right="1rem",
                display={
                    "base": "none",
                    "md": "block"
                },
            ),
            # Middle: Connector Line and Marker
            rx.box(
                rx.box(
                    width="10px",
                    height="10px",
                    border_radius="50%",
                    background_color="#74452f",
                    margin="0 auto",
                    z_index="1",
                ),
                rx.box(
                    width="2px",
                    flex="1",
                    background_color="#ccc",
                    margin="0 auto",
                ),
                display="flex",
                flex_direction="column",
                align_items="center",
                position="relative",
                width="20px",  # Set a fixed width for the marker column
            ),
            # Right side: Content
            rx.box(
                rx.image(
                    src=image_url,
                    fallback=placeholder_url,
                    width="100%",
                    height="auto",
                    border_radius="1rem",
                    margin_bottom="0.5rem",
                    object_fit="cover",
                ),
                rx.text(
                    event_data["description"],
                    padding="0.5rem 1rem",
                    color="#555",
                ),
                flex="1",  # Allow content to take up remaining space
            ),
            align_items="flex-start",
            width="100%",
        ),
        flex_direction={
            "base": "column",
            "md": "row"
        },
        margin_bottom="2rem",
        position="relative",
        width="100%",
    )


# Main Family Memories Page with Vertical Timeline
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
                "Capture and relive your most cherished moments with your loved ones! Share anything.",
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
        rx.vstack(
            rx.foreach(
                FamilyState.data,
                TimelineEvent
            ),
            display="flex",
            flex_direction="column",
            position="relative",
            _before={
                "content": '""',
                "position": "absolute",
                "top": "0",
                "width": "2px",
                "height": "100%",
                "background_color": "#ccc",
                "left": "228px"
            },
            width="100%",
            max_width="1000px",
            margin_left="auto",
            margin_right="auto",
            padding="2rem",
        ),
        width="100%",
        max_width="1280px",
        margin_left="auto",
        margin_right="auto",
        padding="2rem",
    )
    return create_themed_page(content)


# State Management for Adding a New Memory
class NewMemory(rx.State):
    date: str = ""
    description: str = ""
    generated_uuid: str = ""

    def handle_submit(self, form_data: dict) -> None:
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

        # Store document with date and description
        docs = f"{self.date}|{self.description}|",

        collection.upsert(
            documents=docs,
            metadatas=[{"filename": self.generated_uuid}],
            ids=[self.generated_uuid],
        )

        return rx.redirect("/family")

    async def handle_upload(self, files: List[rx.UploadFile]) -> None:
        collection = chromadb.HttpClient(
            host='localhost', port=8001
        ).get_or_create_collection(
            name="vectordb",
            embedding_function=GeminiEmbeddingFunction()
        )

        for file in files:
            upload_data = await file.read()
            outfile = f"{rx.get_upload_dir()}/{self.generated_uuid}.jpg"

            try:
                image = Image.open(io.BytesIO(upload_data))
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(outfile, format="JPEG")
            except Exception as e:
                print(f"Error saving image: {e}")
                continue

            # Append the image description to the existing document
            result_text = "No description available."  # Default value

            try:
                myfile = genai.upload_file(outfile, mime_type="image/jpeg")
                result = text_to_img_model.generate_content(
                    [myfile, "\n\n", "Please give me a description of this image as detailed as possible"]
                )
                result_text = result.get("text", "No description available.")
            except Exception as e:
                print(f"Error generating image description: {e}")

            old_data = collection.get(ids=[self.generated_uuid])
            docs = f"{old_data['documents'][0]}|{result_text}",

            collection.upsert(
                documents=docs,
                metadatas=[{"filename": self.generated_uuid}],
                ids=[self.generated_uuid],
            )


# Page for Adding a New Memory
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
                                    lambda file: rx.text(file, color="#4B5563")
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
