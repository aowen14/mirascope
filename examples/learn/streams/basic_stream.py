from mirascope.core import openai, prompt_template


@openai.call(model="gpt-4o-mini", stream=True)
@prompt_template("Recommend a {genre} book")
def recommend_book(genre: str): ...


for chunk, _ in recommend_book("fantasy"):
    print(chunk.content, end="", flush=True)
