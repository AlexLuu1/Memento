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

genai.configure(api_key='AIzaSyBoWysd4slrqHZUjZe7i9PJPSl4YugAxeI')
text_to_img_model = genai.GenerativeModel("gemini-1.5-flash")


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = 'models/embedding-001'
        title = "Custom query"
        return genai.embed_content(model=model,
                                    content=input,
                                    task_type="retrieval_document",
                                    title=title)["embedding"]


class FamilyState(rx.State):
    data: List[tuple[str, str]] = []

    def get_data(self):
        self.data = []
        collection = chromadb.HttpClient(host='localhost', port=8001).get_or_create_collection(name="vectordb", embedding_function=GeminiEmbeddingFunction())
        results = collection.get()

        documents = results["documents"]
        metadatas = results["metadatas"]

        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            print(doc)
            date, description, image_summary = doc.split('|', 2)
            self.data.append((description, metadata['filename'] + ".jpg"))
        print(self.data)
    

def single_render(single_data: tuple):
    return rx.container(
        rx.card(
            rx.hstack(
                rx.image(
                    src=rx.get_upload_url(single_data[1]),
                    width="200px",
                    height="auto",
                ),
                rx.text(single_data[0]),
            ),
        ),
    )


@rx.page(on_load=FamilyState.get_data, route="/family")
def family_index():
    return rx.container(
        rx.spacer(),
        rx.vstack(
            rx.heading("Family", size="9"),
            rx.text(
                "Add new memories, here!",
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
                FamilyState.data,
                single_render
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
    generated_uuid = ""

    def handle_submit(self, form_data: dict):
        self.date = form_data["date"]
        self.description = form_data["description"]

        # chroma run --path ./db_path --host localhost --port 8001
        collection = chromadb.HttpClient(host='localhost', port=8001).get_or_create_collection(name="vectordb", embedding_function=GeminiEmbeddingFunction())

        self.generated_uuid = str(uuid.uuid4())
        
        docs = f"""{self.date}|{self.description}""",  # TODO: add prompt engineering stuff

        collection.upsert(
            documents=docs,
            metadatas=[{"filename": self.generated_uuid}],
            ids=[self.generated_uuid],
        )

        old_data = collection.get(
            ids=[self.generated_uuid]
        )
        print("1st function data", old_data)

        return rx.redirect(
            "/family"
        )
    
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle the upload of file(s).

        Args:
            files: The uploaded files.
        """
        collection = chromadb.HttpClient(host='localhost', port=8001).get_or_create_collection(name="vectordb", embedding_function=GeminiEmbeddingFunction())

        for file in files:
            upload_data = await file.read()
            outfile = f"{rx.get_upload_dir()}/{self.generated_uuid}.jpg"

            print(outfile)

            # Save the file.
            # with outfile.open("wb") as file_object:
            
            image = Image.open(io.BytesIO(upload_data))
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Save the image as a JPG
            # jpg_image_io = io.BytesIO()
            image.save(outfile, format="JPEG")

            # file_object.write(upload_data)
            
            # Get text from image with Gemini
            myfile = genai.upload_file(outfile, mime_type="image/jpeg")
            print(f"{myfile=}")

            result = text_to_img_model.generate_content(
                [myfile, "\n\n", "Please give me a description of this image as detailed as possible"]
            )
            print(f"{result.text=}")

            old_data = collection.get(
                ids=[self.generated_uuid]
            )
            print("1st function old data", old_data)

            docs = f"""{old_data["documents"][0]}|{result.text}""",  # TODO: add prompt engineering stuff

            collection.upsert(
                documents=docs,
                metadatas=[{"filename": self.generated_uuid}],
                ids=[self.generated_uuid],
            )

            old_data = collection.get(
                ids=[self.generated_uuid]
            )
            print("2nd function data", old_data)


@rx.page(route="/family/new-memory")
def add_new_memory():
    return rx.container(
        rx.vstack(
            rx.spacer(),
            rx.heading("Add A New Memory", size="8"),
            rx.spacer(spacing="9"),
        ),
        rx.form(
            rx.vstack(
                rx.text(
                    "Enter the date this memory occurred:",
                    size="5",
                ),
                rx.input(
                    name="date",
                    placeholder="Enter date...",
                    type="date",
                    required=True,
                ),
                rx.text(
                    "Enter the description of the memory:",
                    size="5",
                ),
                rx.text_area(
                    name="description",
                    placeholder="Enter description...",
                    type="text",
                    required=True,
                    resize="both",
                    auto_height=True,
                    width="100%",
                ),
                rx.text(
                    "Upload a picture of the memory:",
                    size="5",
                ),
                rx.upload(
                    rx.vstack(
                        rx.button(
                            "Select File",
                            color="black",
                            bg="white",
                            border=f"1px solid black",
                            type="button"
                        ),
                        rx.text(
                            "Drag and drop files here or click to select files"
                        ),
                    ),
                    id="upload1",
                    border=f"1px dotted black",
                    padding="3em",
                ),
                rx.hstack(
                    rx.foreach(
                        rx.selected_files("upload1"), rx.text
                    )
                ),
                rx.button("Submit", type="submit"),
                width="100%",
            ),
            on_submit=[NewMemory.handle_submit, 
                       NewMemory.handle_upload(rx.upload_files(upload_id="upload1"))
                    ],
            reset_on_submit=True,
        ),
        rx.spacer(),
    )