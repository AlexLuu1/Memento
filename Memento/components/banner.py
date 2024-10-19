import reflex as rx
from rxconfig import config

class TopBannerBasic(rx.ComponentState):
    hide: bool = False

    def toggle(self):
        self.hide = not self.hide

    @classmethod
    def get_component(cls, **props):
        return rx.cond(
            ~cls.hide,
            rx.hstack(
                rx.flex(
                    rx.badge(
                        rx.icon("megaphone", size=18),
                        padding="0.30rem",
                        radius="full",
                    ),
                    rx.text(
                        "ReflexCon 2024 - ",
                        rx.link(
                            "Join us at the event!",
                            href="#",
                            underline="always",
                            display="inline",
                            underline_offset="2px",
                        ),
                        weight="medium",
                    ),
                    align="center",
                    margin="auto",
                    spacing="3",
                ),
                rx.icon(
                    "x",
                    cursor="pointer",
                    justify="end",
                    flex_shrink=0,
                    on_click=cls.toggle,
                ),
                wrap="nowrap",
                # position="fixed",
                justify="between",
                width="100%",
                # top="0",
                align="center",
                left="0",
                # z_index="50",
                padding="1rem",
                background=rx.color("accent", 4),
                **props,
            ),
            # Remove this in production
            rx.icon_button(
                rx.icon("eye"),
                cursor="pointer",
                on_click=cls.toggle,
            ),
        )


top_banner_basic = TopBannerBasic.create