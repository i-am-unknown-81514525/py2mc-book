# py2mc-book
This is a project to use python code to generate custom written book (e.g. custom format, hover event, click event...) command. This is comaptible to Minecraft 1.20.4
You are welcome to create an issue or propose a big fix if anything occured.

# Example
```python
book = Book(author='Someone', title='Mystery Book')
page = Page()
page.add_component(
    TextComponent(
        text='[Go to Google]',
        click_event=ClickEvent(action=ClickAction.URL, value='https://google.com'),
        attribute=StringFormat(underline=True, italic=True), color='blue')
)
book.add_page(page)
print(book.give_cmd('@s', 1))
# /give @s minecraft:written_book{author:"Someone", title: "Mystery Book", pages: ['["", {"color": "blue", "clickEvent": {"action": "open_url", "value": "https://google.com"}, "italic": True, "underline": True, "text": "[Go to Google]", "type": "text"}]']} 1
```
