from urllib.request import urlopen

import reflex as rx

from reflex_audio_capture import AudioRecorderPolyfill, get_codec, strip_codec_part

import os
from groq import Groq
from deepgram import (
    DeepgramClient,
    SpeakOptions,
)

import chromadb

from chromadb import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
import re

from .components import *

client = Groq(api_key=os.environ['GROQ_API_KEY'])
deepgram = DeepgramClient(os.environ['DEEPGRAM_API_KEY'])
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

REF = "myaudio"

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
        width="100%"
    )
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = 'models/embedding-001'
        title = "Custom query"
        return genai.embed_content(model=model,
                                   content=input,
                                   task_type="retrieval_document",
                                   title=title)["embedding"]


class UserState(rx.State):
    """The app state."""

    has_error: bool = False
    processing: bool = False
    transcript: list[str] = []
    device_id: str = ""
    use_mp3: bool = True
    tts_output_file: str = ""
    is_talking: bool = False

    img_to_display: str = ""
    text_output: str = ""
    filenum: int = 0

    history: list[tuple[str, str]] = []

    def get_data(self):
        self.transcript = []
        self.text_output = ""
        self.img_to_display = ""
        self.history = []

    async def on_data_available(self, chunk: str):
        mime_type, _, codec = get_codec(chunk).partition(";")
        audio_type = mime_type.partition("/")[2]
        if audio_type == "mpeg":
            audio_type = "mp3"
        with urlopen(strip_codec_part(chunk)) as audio_data:
            try:
                self.processing = True
                yield
                transcription = client.audio.transcriptions.create(
                    # Required audio file
                    file=(("temp." + audio_type, audio_data.read(), mime_type)),
                    model="whisper-large-v3-turbo",  # Required model to use for transcription
                    prompt="Specify context or spelling",  # Optional
                    response_format="json",  # Optional
                    language="en",  # Optional
                    temperature=0.0  # Optional
                )
            except Exception as e:
                self.has_error = True
                yield capture.stop()
                raise
            finally:
                self.processing = False
            self.transcript.append(transcription.text)

        # Get Documents
        collection = chromadb.HttpClient(host='localhost', port=8001).get_or_create_collection(
            name="vectordb", embedding_function=GeminiEmbeddingFunction())
        results = collection.query(
            query_texts=[" ".join(self.transcript)],
            n_results=10,
        )
        print(results)

        # Prompt LLM
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        output = ""
        # Iterate through the
        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            # Split the document into date and description
            date, description, image_summary = doc.split('|', 2)
            filename = metadata["filename"]

            # Add the formatted data to the result string
            output += f"""
            <memory{i}>
            Date: {date}
            Description: {description}
            ImageName: {filename}
            Image Summary: {image_summary}
            </memory{i}>
            """
        output = output.strip()

        system = f"""
        You are Memento, a memory storage AI designed for elderly individuals in nursing homes.
        Your role is to help elderly users recall cherished memories by using voice recognition technology. 
        When an elderly user speaks about a memory, you retrieve and display relevant images that are stored in the system.
        When an elderly user speaks about a memory, you don't just passively listen, you actively engage with their narrative. 
        You retrieve and display relevant images, creating a rich, multi-sensory experience that brings their memories to life. 
        Your responses should be carefully crafted based on the specific memory data provided, ensuring a personalized and accurate reflection of each individual's unique life experiences.
        You must always use the `fileNameGrabber` tool call.

        **Your responses should be based on the data provided about the memories**

        # Persona
        <persona>
        - Be Empathetic and Warm
        - Have a Clear Communication
        - Be Nostalgic and Personalized
        - Be Patient and Non-Rushed
        - Keep Your Tone Gentle, Slow-Paced, Comforting
        </persona>

        # Interaction Guidelines
        <guidelines>
        - Always greet the user with a warm welcome.
        - When a memory is mentioned, respond with excitement and genuine interest.
        - Do NOT mention the Image Summary directly, understand the Image Summary paired with the Description to understand the context.
        - Your response should contain about one paragraph long, try to elaborate things mentioned in the Description and Image Summary.
        - If a memory seems emotional, acknowledge the user's feelings with empathy.
        - Ask gentle follow-up questions to encourage more storytelling.
        - End each interaction on a positive note.
        </guidelines>

        # Memories Data
        <data>
        {output}
        </data>
        """

        def fileNameGrabber(image_name: str) -> str:
            """Grabs the Image Name of the most relevant memory created in your response.

            Args:
                image_name: Light level from 0 to 100. Zero is off and 100 is full brightness

            Returns:
                A string containing the image_name of the most relevant memory in your response.
            """
            return image_name

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system,
            tools=[fileNameGrabber]
        )

        # Get History
        history = []
        for item in self.history:
            history.append({"role": "user", "parts": item[0]})
            history.append({"role": "model", "parts": item[1]})

        # Reset
        self.text_output = ""
        self.img_to_display = ""
        
        # Run LLM
        chat = model.start_chat(
            history=history
        ) 
        response = chat.send_message(self.transcript[-1])

        # Get Text
        self.text_output = response.candidates[-1].content.parts[0].text
        self.is_talking = True
        print(self.text_output)

        # Save history
        self.history.append((self.transcript[-1], self.text_output))

        # Get image tool call
        if len(response.candidates[-1].content.parts) > 1:
            text = response.candidates[-1].content.parts[1].function_call.__str__()
            pattern = r'string_value:\s*"([a-f0-9-]+)"'
            self.img_to_display = f"{re.search(pattern, text).group(1)}.jpg"
            print("Image Name:", self.img_to_display)
        else:
            self.img_to_display = ""

    def set_device_id(self, value):
        self.device_id = value
        yield capture.stop()

    def on_error(self, err):
        print(err)

    def on_load(self):
        # We can start the recording immediately when the page loads
        return capture.start()

    def reset_output(self):
        # self.text_output = ""
        # self.img_to_display = ""
        self.filenum += 1
        self.is_talking = False

    @rx.var(cache=True)
    def get_tts(self) -> str:
        if not self.text_output:
            return ""

        print("LLM Output: " + self.text_output)
        SPEAK_OPTIONS = {"text": self.text_output}
        self.tts_output_file = f"tts_output_{self.filenum}.wav"
        options = SpeakOptions(
            model="aura-asteria-en",
            encoding="linear16",
            container="wav"
        )

        deepgram.speak.v("1").save(f"uploaded_files/{self.tts_output_file}", SPEAK_OPTIONS, options)
        return self.tts_output_file


capture = AudioRecorderPolyfill.create(
    id=REF,
    on_data_available=UserState.on_data_available,
    on_error=UserState.on_error,
    device_id=UserState.device_id,
    use_mp3=UserState.use_mp3,
)


def input_device_select():
    return rx.select.root(
        rx.select.trigger(placeholder="Select Input Device"),
        rx.select.content(
            rx.foreach(
                capture.media_devices,
                lambda device: rx.cond(
                    device.deviceId & device.kind == "audioinput",
                    rx.select.item(device.label, value=device.deviceId),
                ),
            ),
        ),
        on_change=UserState.set_device_id,
    )

@rx.page(on_load=UserState.get_data, route="/user")
def user_index() -> rx.Component:
    def mic_button(is_recording: bool):
        return rx.button(
            rx.icon(
                tag="mic",
                color="white",
                size=32,  # Increased icon size
            ),
            on_click=capture.stop() if is_recording else capture.start(),
            bg="red" if is_recording else "blue.500",
            color="white",
            border_radius="full",
            width="80px",  # Set a fixed width
            height="80px",  # Set a fixed height equal to width for perfect circle
            p="0",  # Remove padding
            _hover={"bg": "red.600" if is_recording else "blue.600"},
            is_loading=is_recording,
            spinner_placement="center",
        )

    content = rx.center(
        rx.vstack(
            create_custom_heading(
                heading_type="h2",
                font_size="2.5rem",
                margin_bottom="0rem",
                heading_text="Learn What Your Family Is Doing!",
            ),
            capture,
            rx.divider(width="100%", border_color="#A9A9A9", border_width="2px", margin_y="1.5rem"),
            rx.box(
                rx.cond(
                    capture.is_recording,
                    mic_button(True),
                    mic_button(False)
                ),
                margin_y="2em",  # Add some vertical margin
            ),
            rx.vstack(
                rx.cond(
                    UserState.transcript[-1] != "",
                    rx.box(
                        rx.text("You: ", font_size="1.2rem", font_weight="bold"),
                        rx.text(UserState.transcript[-1], font_size="1.1rem"),
                        rx.cond(
                            UserState.processing,
                            rx.spinner(color="blue", size="sm"),
                        ),
                        border_radius="10px",
                        width="100%",
                        margin_y="12px",
                        padding="16px",
                        border_color="#e0e0e0",
                        border_style="solid",
                        border_width="1px",
                        bg="gray.50",
                    ),
                ),
                rx.cond(
                    UserState.img_to_display != "",
                    rx.image(src=rx.get_upload_url(UserState.img_to_display), width="100%", height="auto"),
                ),
                rx.cond(
                    UserState.is_talking,
                    rx.audio(
                        url=rx.get_upload_url(UserState.get_tts),
                        width="0px",
                        height="0px",
                        playing=True,
                        on_ended=UserState.reset_output
                    ),
                ),
                rx.cond(
                    UserState.text_output != "",
                    rx.box(
                        rx.text("Assistant: ", font_size="1.2rem", font_weight="bold"),
                        rx.text(UserState.text_output, font_size="1.1rem"),
                        border_radius="10px",
                        width="100%",
                        margin_y="12px",
                        padding="16px",
                        border_color="#e0e0e0",
                        border_style="solid",
                        border_width="1px",
                        bg="blue.50",
                    ),
                    rx.box(
                        rx.text("Assistant: ", font_size="1.2rem", font_weight="bold"),
                        border_radius="10px",
                        width="100%",
                        margin_y="12px",
                        padding="16px",
                        border_color="#e0e0e0",
                        border_style="solid",
                        border_width="1px",
                        bg="blue.50",
                    ),
                    
                ),
                width="100%",
                spacing="1em",
                align_items="stretch",
            ),
            width="100%",
            max_width="1000px",
            spacing="1.5em",
            align_items="center",
        ),
        width="100%",
        padding="2em",
    )

    return create_themed_page(content)


# # Add state and page to the app.
# app = rx.App()
# app.add_page(index)
