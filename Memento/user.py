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
    filenum: int = 0
    # process_llm: bool = False

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
            print(doc.split('|', 2))
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
        
        **Your responses should be based on the data provided about the memories**

        # Persona
        <persona>
        - Be Empathetic and Warm
        - Have a Clear and Simple Communication
        - Be Nostalgic and Personalized
        - Be Patient and Non-Rushed
        - Keep Your Tone Gentle, Slow-Paced, Comforting
        </persona>

        # Interaction Guidelines
        <guidelines>
        - Always greet the user by name and with a warm welcome.
        - When a memory is mentioned, respond with excitement and genuine interest.
        - Use phrases like "Oh, what a wonderful memory!" or "I remember you telling me about that before. Let's take a closer look."
        - Describe the images you're displaying, painting a vivid picture with your words.
        - Ask gentle follow-up questions to encourage more storytelling.
        - If a memory seems emotional, acknowledge the user's feelings with empathy.
        - End each interaction on a positive note, expressing gratitude for the shared memory.
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

        print(self.transcript)
        generated = model.generate_content(" ".join(self.transcript))
        print(generated)
        self.text_output = generated.candidates[-1].content.parts[0].text

        text = generated.candidates[-1].content.parts[1].function_call.__str__()
        import re
        pattern = r'string_value:\s*"([a-f0-9-]+)"'
        self.img_to_display = f"{re.search(pattern, text).group(1)}.jpg"
        print("Image Name:", self.img_to_display)

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

    def reset_output(self):
        self.text_output = ""
        self.filenum += 1

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
                UserState.img_to_display != "",
                rx.image(src=rx.get_upload_url(UserState.img_to_display), width="100px", height="auto"),
            ),
            rx.cond(
                UserState.text_output != "",
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
                rx.text(UserState.text_output),
            ),
            style={"width": "100%", "> *": {"width": "100%"}},
        ),
        size="1",
        margin_y="2em",
    )


# # Add state and page to the app.
# app = rx.App()
# app.add_page(index)
