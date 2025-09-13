import discord

# Map your friendly strings -> discord.py component classes
COMPONENT_MAP = {
    "text": discord.ui.TextInput,         # 4
    "user": discord.ui.UserSelect,        # 5
    "role": discord.ui.RoleSelect,        # 6
    "mentionable": discord.ui.MentionableSelect,  # 7
    "channel": discord.ui.ChannelSelect,  # 8
}


class Label(discord.ui.Item):
    def __init__(self, *, label: str, component: discord.ui.Item, description: str | None = None):
        super().__init__()
        self.label = label
        self.description = description
        self.component = component

    def to_component_dict(self):
        data = {
            "type": 18,
            "label": self.label,
            "component": self.component.to_component_dict(),
        }
        if self.description:
            data["description"] = self.description
        return data


class CyModals(discord.ui.Modal):
    def __init__(self, title: str, fields: list[dict], timeout: int = 300):
        """
        fields = [
            {
                "type": "text" | "user" | "role" | "mentionable" | "channel",
                "custom_id": "...",
                "label": "Displayed Label",
                "description": "Optional helper text",
                ...component kwargs...
            }
        ]
        """
        super().__init__(title=title, timeout=timeout)
        self.values = {}

        for field in fields:
            self._add_field(field)

    def _add_field(self, field: dict):
        field_type = field.pop("type").lower()
        comp_cls = COMPONENT_MAP.get(field_type)
        if not comp_cls:
            raise ValueError(f"Unsupported modal field type: {field_type}")

        custom_id = field.pop("custom_id")
        label = field.pop("label", custom_id)
        description = field.pop("description", None)

        component = comp_cls(custom_id=custom_id, **field)
        wrapped = Label(label=label, component=component, description=description)
        self.add_item(wrapped)

    async def on_submit(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, Label):
                inner = child.component
                if hasattr(inner, "value"):   # TextInput
                    self.values[inner.custom_id] = inner.value
                elif hasattr(inner, "values"):  # Selects
                    self.values[inner.custom_id] = inner.values
        await interaction.response.defer()
