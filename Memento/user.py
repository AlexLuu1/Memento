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

# Initialize the Groq client
client = Groq(api_key="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")
deepgram = DeepgramClient("4186faa1b840c8c63f87d22f0f5d6d744ce9f100")
genai.configure(api_key='AIzaSyBoWysd4slrqHZUjZe7i9PJPSl4YugAxeI')

REF = "myaudio"

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
    timeslice: int = 0
    device_id: str = ""
    use_mp3: bool = True
    tts_output_file: str = ""

    img_to_display: str = ""
    text_output: str = ""
    process_llm: bool = False

    async def on_data_available(self, chunk: str):
        mime_type, _, codec = get_codec(chunk).partition(";")
        audio_type = mime_type.partition("/")[2]
        if audio_type == "mpeg":
            audio_type = "mp3"
        print(len(chunk), mime_type, codec, audio_type)
        with urlopen(strip_codec_part(chunk)) as audio_data:
            print(type(audio_data))
            try:
                self.processing = True
                yield
                transcription = client.audio.transcriptions.create(
                   file=(("temp." + audio_type, audio_data.read(), mime_type)), # Required audio file
                   model="whisper-large-v3-turbo", # Required model to use for transcription
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
        collection = chromadb.HttpClient(host='localhost', port=8001).get_or_create_collection(name="vectordb", embedding_function=GeminiEmbeddingFunction())
        results = collection.query(
            query_texts=[" ".join(self.transcript)],
            n_results=10,
        )
        print(results)

        # Prompt LLM
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        output = ""
        # Iterate through the documents
        for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
            print(doc)
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
        Your responses should be based on the data provided about the memories
        
        # Persona
        <persona>
        - Be Empathetic and Warm
        - Have a Clear and Simple Communication
        - Be Nostalgic and Personalized
        - Be Patient and Non-Rushed
        - Keep Your Tone Gentle, Slow-Paced, Comforting
        </persona>

        # Memories Data
        <data>
        {output}
        </data>
        """

        print(system)

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

        generated = model.generate_content(" ".join(self.transcript))

        self.text_output = generated._result.candidates["content"]["parts"][0]["text"]
        print(self.text_output)
        
        self.img_to_display = f"/uploaded_files/{generated._result.candidates['content']['parts'][1]['function_call']['args']['image_name']}"
        print(self.img_to_display)
        

    def set_timeslice(self, value):
        self.timeslice = value[0]

    def set_device_id(self, value):
        self.device_id = value
        yield capture.stop()

    def on_error(self, err):
        print(err)

    def on_load(self):
        # We can start the recording immediately when the page loads
        return capture.start()
    
    @rx.var
    def get_tts(self)->str:
        self.process_llm = False
        SPEAK_OPTIONS = {"text": "Hello, how can I help you today?"}
        self.tts_output_file = "assets/tts_output.mp3"
        options = SpeakOptions(
            model="aura-asteria-en",
        )

        response = deepgram.speak.v("1").save(self.tts_output_file, SPEAK_OPTIONS, options)
        # self.process_inputs = False
        # self.process_outputs = False
        return "/tts_output.mp3"#self.tts_output_file


capture = AudioRecorderPolyfill.create(
    id=REF,
    on_data_available=UserState.on_data_available,
    on_error=UserState.on_error,
    timeslice=UserState.timeslice,
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


def user_index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("OpenAI Whisper Demo"),
            rx.card(
                rx.vstack(
                    f"Timeslice: {UserState.timeslice} ms",
                    rx.slider(
                        min=0,
                        max=10000,
                        value=[UserState.timeslice],
                        on_change=UserState.set_timeslice,
                    ),
                    rx.cond(
                        capture.media_devices,
                        input_device_select(),
                    ),
                ),
            ),
            capture,
            rx.text(f"Recorder Status: {capture.recorder_state}"),
            rx.cond(
                capture.is_recording,
                rx.button("Stop Recording", on_click=capture.stop()),
                rx.button(
                    "Start Recording",
                    on_click=capture.start(),
                ),
            ),
            rx.card(
                rx.text("Transcript"),
                rx.divider(),
                rx.foreach(
                    UserState.transcript,
                    rx.text,
                ),
                rx.cond(
                    UserState.processing,
                    rx.text("..."),
                ),
            ),
            rx.cond(
               UserState.process_llm,
               rx.audio(
                    url=UserState.get_tts,
                    width="0px",
                    height="0px",   
                    playing=True
                ),
            ),
            rx.cond(
                UserState.img_to_display != "",
                rx.image(src=UserState.img_to_display, width="100px", height="auto"),
            ),
            style={"width": "100%", "> *": {"width": "100%"}},
        ),
        size="1",
        margin_y="2em",
    )


# # Add state and page to the app.
# app = rx.App()
# app.add_page(index)