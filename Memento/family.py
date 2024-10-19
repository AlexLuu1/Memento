import reflex as rx
from rxconfig import config
from datetime import datetime

from PIL import Image
import requests
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
import uuid

genai.configure(api_key='AIzaSyBoWysd4slrqHZUjZe7i9PJPSl4YugAxeI')
text_to_img_model = genai.GenerativeModel("gemini-1.5-flash")


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


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = 'models/embedding-001'
        title = "Custom query"
        return genai.embed_content(model=model,
                                    content=input,
                                    task_type="retrieval_document",
                                    title=title)["embedding"]

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
        
        docs = f"""
            {self.date}
            {self.description}
        """,  # TODO: add prompt engineering stuff

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
            outfile = rx.get_upload_dir() / file.filename

            # Save the file.
            with outfile.open("wb") as file_object:
                file_object.write(upload_data)
            
            # Get text from image with Gemini
            myfile = genai.upload_file(outfile)
            print(f"{myfile=}")

            result = text_to_img_model.generate_content(
                [myfile, "\n\n", "Please give me a concise description of this image"]
            )
            print(f"{result.text=}")

            old_data = collection.get(
                ids=[self.generated_uuid]
            )
            print("1st function old data", old_data)

            docs = f"""
                {old_data["documents"][0]}
                {result.text}
            """,  # TODO: add prompt engineering stuff

            collection.upsert(
                documents=docs,
                metadatas=[{"filename": self.generated_uuid}],
                ids=[self.generated_uuid],
            )

            old_data = collection.get(
                ids=[self.generated_uuid]
            )
            print("2nd function data", old_data)



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