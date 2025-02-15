import asyncio
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pydantic import BaseModel

from mirascope.core import BaseMessageParam, openai, prompt_template


def extract_content(url: str) -> str:
    """Extract the main content from a webpage.

    Args:
        url: The URL of the webpage to extract the content from.

    Returns:
        The extracted content as a string.
    """
    try:
        response = requests.get(url, timeout=5)

        soup = BeautifulSoup(response.content, "html.parser")

        unwanted_tags = ["script", "style", "nav", "header", "footer", "aside"]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_=re.compile("content|main"))
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        lines = (line.strip() for line in text.splitlines())
        return "\n".join(line for line in lines if line)
    except Exception as e:
        return f"{type(e)}: Failed to extract content from URL {url}"


class WebAssistant(BaseModel):
    messages: list[BaseMessageParam | openai.OpenAIMessageParam] = []
    search_history: list[str] = []
    max_results_per_query: int = 2

    def _web_search(self, queries: list[str]) -> str:
        """Performs web searches for given queries and returns URLs.

        Args:
            queries: List of search queries.

        Returns:
            str: Newline-separated URLs from search results or error messages.

        Raises:
            Exception: If web search fails entirely.
        """
        try:
            urls = []
            for query in queries:
                results = DDGS(proxies=None).text(
                    query, max_results=self.max_results_per_query
                )

                for result in results:
                    link = result["href"]
                    try:
                        urls.append(link)
                    except Exception as e:
                        urls.append(
                            f"{type(e)}: Failed to parse content from URL {link}"
                        )
                self.search_history.append(query)
            return "\n\n".join(urls)

        except Exception as e:
            return f"{type(e)}: Failed to search the web for text"

    @openai.call(model="gpt-4o-mini", stream=True)
    @prompt_template(
        """
        SYSTEM:
        You are an expert web searcher. Your task is to answer the user's question using the provided tools.
        The current date is {current_date}.

        You have access to the following tools:
        - `_web_search`: Search the web when the user asks a question. Follow these steps for EVERY web search query:
            1. There is a previous search context: {self.search_history}
            2. There is the current user query: {question}
            3. Given the previous search context, generate multiple search queries that explores whether the new query might be related to or connected with the context of the current user query. 
                Even if the connection isn't immediately clear, consider how they might be related.
        - `extract_content`: Parse the content of a webpage.

        When calling the `_web_search` tool, the `body` is simply the body of the search
        result. You MUST then call the `extract_content` tool to get the actual content
        of the webpage. It is up to you to determine which search results to parse.

        Once you have gathered all of the information you need, generate a writeup that
        strikes the right balance between brevity and completeness based on the context of the user's query.

        MESSAGES: {self.messages}
        USER: {question}
        """
    )
    async def _stream(self, question: str) -> openai.OpenAIDynamicConfig:
        return {
            "tools": [self._web_search, extract_content],
            "computed_fields": {
                "current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
        }

    async def _step(self, question: str):
        print(self.messages)
        response = await self._stream(question)
        tools_and_outputs = []
        async for chunk, tool in response:
            if tool:
                print(f"using {tool._name()} tool with args: {tool.args}")
                tools_and_outputs.append((tool, tool.call()))
            else:
                print(chunk.content, end="", flush=True)
        if response.user_message_param:
            self.messages.append(response.user_message_param)
        self.messages.append(response.message_param)
        if tools_and_outputs:
            self.messages += response.tool_message_params(tools_and_outputs)
            await self._step("")

    async def run(self):
        while True:
            question = input("(User): ")
            if question == "exit":
                break
            print("(Assistant): ", end="", flush=True)
            await self._step(question)
            print()


if __name__ == "__main__":
    web_assistant = WebAssistant()
    asyncio.run(web_assistant.run())
# Output:
"""
(User): What are the top 5 smartphones
(Assistant): 1. **iPhone 15 Pro Max**
     - **Best Overall:**
       - The iPhone 15 Pro Max offers a powerful A17 chipset, a versatile camera system with a 5x zoom telephoto lens, and a premium design with titanium sides. It's noted for its remarkable battery life and robust performance.

  2. **Samsung Galaxy S24 Ultra**
     - **Best Samsung Phone:**
       - The Galaxy S24 Ultra features a Qualcomm Snapdragon 8 Gen 3 processor, a stunning OLED display, and a highly capable camera system with a new 50MP shooter for 5x zoom. It stands out for its AI capabilities and impressive battery life.

  3. **Google Pixel 8 Pro**
     - **Smartest Camera:**
       - The Pixel 8 Pro is celebrated for its AI-driven photo-editing features, including Magic Editor and Magic Audio Eraser. It sports a Tensor G3 chip, a high-resolution display, and enhanced camera sensors, providing excellent low-light performance and a support period extending to seven years of updates.

  4. **Google Pixel 8a**
     - **Best Under $500:**
       - The Pixel 8a delivers high performance with its Tensor G3 chipset, a bright OLED display, and strong camera capabilities for its price range. It also offers Google's AI features and promises seven years of updates, making it an excellent budget option.

  5. **iPhone 15**
     - **Best iPhone Value:**
       - The iPhone 15 includes a 48MP main camera, supports USB-C, and features Apple's A16 Bionic chipset. It provides good value with solid performance, camera quality, and a user-friendly experience.

  These smartphones have been chosen based on their overall performance, camera capabilities, battery life, and additional features like AI integration and long-term software support.
"""
