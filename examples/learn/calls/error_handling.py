from openai import OpenAIError

from mirascope.core import openai, prompt_template


@openai.call(model="gpt-4o-mini")
@prompt_template("Recommend a {genre} book")
def recommend_book(genre: str): ...


try:
    response = recommend_book("fantasy")
    print(response.content)
except OpenAIError as e:
    print(f"Error: {str(e)}")
