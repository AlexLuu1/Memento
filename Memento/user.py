from urllib.request import urlopen

import reflex as rx

from reflex_audio_capture import AudioRecorderPolyfill, get_codec, strip_codec_part

import os
from groq import Groq

# Initialize the Groq client
client = Groq(api_key="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")

REF = "myaudio"


class UserState(rx.State):
    """The app state."""

    has_error: bool = False
    processing: bool = False
    transcript: list[str] = []
    timeslice: int = 0
    device_id: str = ""
    use_mp3: bool = True

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
                transcription = await client.audio.transcriptions.create(
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
            style={"width": "100%", "> *": {"width": "100%"}},
        ),
        size="1",
        margin_y="2em",
    )


# # Add state and page to the app.
# app = rx.App()
# app.add_page(index)