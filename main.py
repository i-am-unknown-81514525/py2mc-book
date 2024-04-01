from __future__ import annotations

import types
from typing import Optional, Union, Sequence, TypeGuard, NoReturn, Any, AnyStr
from abc import ABC, abstractmethod
from dataclasses import dataclass
import string
from enum import Enum

COLOR = (
    "black", "dark_blue", "dark_green", "dark_red", "dark_purple", "gold", "gray", "dark_gray", "blue", "green", "aqua",
    "red", "light_purple", "yellow", "white")


@dataclass
class StringFormat:
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underlined: Optional[bool] = None
    strikethrough: Optional[bool] = None
    obfuscated: Optional[bool] = None
    font: Optional[AnyStr] = None

    def to_dict(self) -> dict[str, Union[bool, AnyStr]]:
        data = {k: v for k, v in self.__dict__.items() if v is not None}
        return data


def color_error(color: AnyStr) -> NoReturn:
    raise ValueError(f"Color '{color}' cannot not be identify and parse")


class BaseComponent(ABC):
    @abstractmethod
    def translate(self) -> NoReturn:
        raise NotImplementedError


class RawComponent(BaseComponent):
    def __init__(self, raw_data):
        self._raw_data = raw_data

    def translate(self) -> Any:
        return self._raw_data


class ClickAction(Enum):
    URL = "open_url"
    FILE = "open_file"
    RUN_CMD = "run_command"
    SUGGEST = "suggest_command"
    CHANGE_PAGE = "change_page"
    COPY = "copy_to_clipboard"


class HoverAction(Enum):
    TEXT = "show_text"
    ITEM = "show_item"
    ENTITY = "show_entity"


class BaseHoverContent(ABC):
    @abstractmethod
    def translate(self) -> NoReturn:
        raise NotImplementedError


class ClickEvent:
    def __init__(self, action: ClickAction, value: AnyStr):
        self._action: ClickAction = action
        self._value = value

    def to_dict(self) -> Any:
        return {'action': self._action.value, 'value': self._value}


@dataclass
class Item:
    id: str
    count: Optional[int] = None
    tag: Optional[Any] = None

    def to_dict(self) -> dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items() if v is not None}
        return data


@dataclass
class Entity:
    type: AnyStr
    uuid: str
    name: Optional[Union[str, TextComponent]] = None

    def to_dict(self) -> dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items() if v is not None}
        return data


class HoverEvent:
    def __init__(self, contents: Union[TextComponent, Item, Entity]):
        if isinstance(contents, TextComponent):
            self._contents = contents
            self._action = HoverAction.TEXT
        elif isinstance(contents, Item):
            self.contents = contents
            self._action = HoverAction.ITEM
        elif isinstance(contents, Entity):
            self._contents = contents
            self._action = HoverAction.ENTITY
        else:
            raise ValueError(f'Invalid contents type: {type(contents)}')

    def to_dict(self) -> dict[str, Any]:
        if isinstance(self._contents, TextComponent):
            return {"action": self._action.value, "contents": self._contents.translate()}
        if isinstance(self._contents, Item):
            return {"action": self._action.value, "contents": self._contents.to_dict()}
        if isinstance(self._contents, Entity):
            return {"action": self._action.value, "contents": self._contents.to_dict()}


class AnyComponent(BaseComponent):
    def __init__(self, color: Optional[AnyStr] = None, attribute: Optional[StringFormat] = None,
                 hover_event: Optional[HoverEvent] = None, click_event: Optional[ClickEvent] = None):
        if not isinstance(color, (str, types.NoneType)):
            color_error('Unknown Color')
        if isinstance(color, str):
            if color.startswith('#'):
                if len(color) != 7:
                    color_error(color)
                for char in color[1:]:
                    if char not in string.hexdigits:
                        color_error(color)
            else:
                if color not in COLOR:
                    color_error(color)
        self._color: Optional[AnyStr] = color
        self._char_attribute: Optional[StringFormat] = attribute
        self._hover_event: Optional[HoverEvent] = hover_event
        self._click_event: Optional[ClickEvent] = click_event

    def translate(self) -> dict[str, Any]:
        data = {}
        if self._color:
            data['color'] = self._color
        if self._hover_event:
            data['hoverEvent'] = self._hover_event.to_dict()
        if self._click_event:
            data['clickEvent'] = self._click_event.to_dict()
        if self._char_attribute:
            return {**data, **self._char_attribute.to_dict()}
        return data


class TextComponent(AnyComponent):
    def __init__(self, text: AnyStr, color: Optional[AnyStr] = None, attribute: Optional[StringFormat] = None,
                 hover_event: Optional[HoverEvent] = None, click_event: Optional[ClickEvent] = None):
        self._text = text
        super().__init__(color, attribute, hover_event, click_event)

    def translate(self) -> dict[str, Any]:
        return {**super().translate(), **{'text': self._text, "type": "text"}}


class TranslatableComponent(AnyComponent):
    def __init__(self, translate: AnyStr, color: Optional[AnyStr] = None, attribute: Optional[StringFormat] = None,
                 hover_event: Optional[HoverEvent] = None, click_event: Optional[ClickEvent] = None,
                 fallback: Optional[AnyStr] = None, with_json: Optional[TextComponent] = None):
        self._translate = translate
        self._fallback = fallback
        self._with_json = with_json
        super().__init__(color, attribute, hover_event, click_event)

    def self_translate(self):
        data = {}
        if self._fallback:
            data['fallback'] = self._fallback
        if self._with_json:
            data['with'] = self._with_json.translate()

    def translate(self) -> dict[str, Any]:
        return {**super().translate(), **{'translate': self._translate, "type": "translatable"},
                **self.self_translate()}


class ScoreComponent(AnyComponent):
    def __init__(self, name: AnyStr, objective: AnyStr, color: Optional[AnyStr] = None,
                 attribute: Optional[StringFormat] = None, hover_event: Optional[HoverEvent] = None,
                 click_event: Optional[ClickEvent] = None):
        self._name = name
        self._objective = objective
        super().__init__(color, attribute, hover_event, click_event)

    def translate(self) -> dict[str, Any]:
        return {**super().translate(), **{'score': {'name': self._name, 'objective': self._objective}, "type": "score"}}


class EntityComponent(AnyComponent):
    def __init__(self, selector: AnyStr, color: Optional[AnyStr] = None, attribute: Optional[StringFormat] = None,
                 hover_event: Optional[HoverEvent] = None, click_event: Optional[ClickEvent] = None,
                 separator: Optional[TextComponent] = None):
        self._selector = selector
        self._seperator = separator
        super().__init__(color, attribute, hover_event, click_event)

    def translate(self) -> dict[str, Any]:
        data = {**super().translate(), **{"type": "selector", "selector": self._selector}}
        if self._seperator:
            data['seperator'] = self._seperator.translate()
        return data


class KeybindComponent(AnyComponent):
    def __init__(self, keybind: dict, color: Optional[AnyStr] = None, attribute: Optional[StringFormat] = None,
                 hover_event: Optional[HoverEvent] = None, click_event: Optional[ClickEvent] = None):
        self._keybind = keybind
        super().__init__(color, attribute, hover_event, click_event)

    def translate(self) -> dict[str, Any]:
        return {**super().translate(), **{'keybind': self._keybind, "type": "keybind"}}


class NbtComponent(AnyComponent):
    def __init__(self, nbt: dict, color: Optional[AnyStr] = None, attribute: Optional[StringFormat] = None,
                 hover_event: Optional[HoverEvent] = None, click_event: Optional[ClickEvent] = None):
        self._nbt = nbt
        super().__init__(color, attribute, hover_event, click_event)

    def translate(self) -> dict[str, Any]:
        return {**super().translate(), **{"type": "keybind"}, **self._nbt}


def is_sequence_component(data) -> TypeGuard[Sequence[BaseComponent]]:
    if not isinstance(data, Sequence):
        return False
    for item in data:
        if not isinstance(item, BaseComponent):
            return False
    return True


def is_sequence_page(data) -> TypeGuard[Sequence[Page]]:
    if not isinstance(data, Sequence):
        return False
    for item in data:
        if not isinstance(item, Page):
            return False
    return True


class Page:
    def __init__(self, content: Optional[list[BaseComponent]] = None):
        self._content: list[Any] = [""]
        if content:
            for component in content:
                self.add_component(component)

    def __iadd__(self, other: Union[BaseComponent, Sequence[BaseComponent]]) -> Page:
        return self.add_component(other)

    def __add__(self, other: Union[BaseComponent, Sequence[BaseComponent]]) -> Page:
        left = Page(content=self._content)
        return left.add_component(other)

    def add_component(self, other: Union[BaseComponent, Sequence[BaseComponent]]) -> Page:
        if not isinstance(other, (BaseComponent, Sequence)):
            raise ValueError('You must supply a `BaseComponent`')
        if isinstance(other, BaseComponent):
            self._content.append(other.translate())
        if isinstance(other, Sequence):
            if not is_sequence_component(other):
                raise ValueError('All element must be subclass on `BaseComponent`')
            for item in other:
                self._content.append(item.translate())
        return self

    def __len__(self) -> int:
        return len(self._content) - 1

    def translate(self):
        return str(self._content.copy()).replace("'", '"')


class Book:
    def __init__(self, author: AnyStr, title: AnyStr, pages: Optional[list[Page]] = None):
        self._author = author
        self._title = title
        self._pages: list[Page] = pages or []

    def add_page(self, page: Union[Page, Sequence[Page]]) -> Book:
        if not isinstance(page, (Page, Sequence)):
            raise ValueError('You must supply a `BaseComponent`')
        if isinstance(page, Page):
            self._pages.append(page)
        if isinstance(page, Sequence):
            if not is_sequence_page(page):
                raise ValueError('All element must be subclass on `BaseComponent`')
            for item in page:
                self._pages.append(item)
        return self

    def __len__(self) -> int:
        return len(self._pages)

    def __iadd__(self, other: Union[Page, Sequence[Page]]) -> Book:
        return self.add_page(other)

    def __add__(self, other: Union[Page, Sequence[Page]]) -> Book:
        left = Book(pages=self._pages)
        return left.add_page(other)

    def translate(self):
        return '{' + f'author:\"{self._author}\", title: \"{self._title}\", pages: {[p.translate() for p in self._pages]}' + '}'

    def item(self):
        return 'minecraft:written_book' + self.translate()

    def give_cmd(self, selector: str = '@s', count: int = 1):
        return f'/give {selector} {self.item()} {count}'


if __name__ == '__main__':
    book = Book(author='null', title='Mystery notebook')
    page = Page()
    page.add_component(
        TextComponent(
            text='[Google Search]',
            click_event=ClickEvent(action=ClickAction.URL, value='https://google.com'),
            hover_event=HoverEvent(contents=
                TextComponent(
                    text='Go to https://google.com',
                    color='white',
                    attribute=StringFormat(underlined=True)
                )
            ),
            attribute=StringFormat(underlined=True, italic=True),
            color='blue'
        )
    )
    page.add_component(
        TextComponent(
            text='[Bing Search]',
            click_event=ClickEvent(action=ClickAction.URL, value='https://www.bing.com'),
            hover_event=HoverEvent(contents=
                TextComponent(
                    text='Go to https://www.bing.com',
                    color='white',
                    attribute=StringFormat(underlined=True)
            )
            ),
            attribute=StringFormat(underlined=True, italic=True),
            color='blue'
        )
    )
    book.add_page(page)
    print(book.give_cmd('@s', 1))