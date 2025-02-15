import json

from anthropic.types import MessageParam
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from mirascope.core import anthropic, prompt_template

load_dotenv()


class Query(BaseModel):
    id: int = Field(..., description="ID of the query, this is auto-incremented")
    question: str = Field(
        ...,
        description="The broken down question to be answered to answer the main question",
    )
    dependencies: list[int] = Field(
        description="List of sub questions that need to be answered before asking this question",
    )
    tools: list[str] = Field(
        description="List of tools that should be used to answer the question"
    )


@anthropic.call(
    model="claude-3-5-sonnet-20240620", response_model=list[Query], json_mode=True
)
@prompt_template(
    """
    SYSTEM:
    You are an expert at creating a query plan for a question.
    You are given a question and you need to create a query plan for it.
    You need to create a list of queries that can be used to answer the question.

    You have access to the following tool:
    - get_weather_by_year
    USER:
    {question}
    """
)
def create_query_plan(question: str): ...


def get_weather_by_year(year: int):
    """Made up data to get Tokyo weather by year"""
    if year == 2020:
        data = {
            "jan": 42,
            "feb": 43,
            "mar": 49,
            "apr": 58,
            "may": 66,
            "jun": 72,
            "jul": 78,
            "aug": 81,
            "sep": 75,
            "oct": 65,
            "nov": 55,
            "dec": 47,
        }
    elif year == 2021:
        data = {
            "jan": 45,
            "feb": 48,
            "mar": 52,
            "apr": 60,
            "may": 68,
            "jun": 74,
            "jul": 80,
            "aug": 83,
            "sep": 77,
            "oct": 67,
            "nov": 57,
            "dec": 49,
        }
    else:
        data = {
            "jan": 48,
            "feb": 52,
            "mar": 56,
            "apr": 64,
            "may": 72,
            "jun": 78,
            "jul": 84,
            "aug": 87,
            "sep": 81,
            "oct": 71,
            "nov": 61,
            "dec": 53,
        }
    return json.dumps(data)


@anthropic.call(model="claude-3-5-sonnet-20240620")
@prompt_template(
    """
    MESSAGES:
    {history}
    USER:
    {question}
    """
)
def run(
    question: str, history: list[MessageParam], tools: list[str]
) -> anthropic.AnthropicDynamicConfig:
    tools_fn = [eval(tool) for tool in tools]
    return {"tools": tools_fn}


def execute_query_plan(query_plan: list[Query]):
    results = {}
    for query in query_plan:
        history = []
        for dependency in query.dependencies:
            result = results[dependency]
            history.append({"role": "user", "content": result["question"]})
            history.append({"role": "assistant", "content": result["content"]})
        result = run(query.question, history, query.tools)
        if tool := result.tool:
            output = tool.call()
            results[query.id] = {"question": query.question, "content": output}
        else:
            return result.content
    return results


query_plan = create_query_plan("Compare the weather in Tokyo from 2020 to 2022")
print(query_plan)
# Output:
"""
  [
      Query(
          id=1,
          question="What was the weather like in Tokyo in 2020?",
          dependencies=[],
          tools=["get_weather_by_year"],
      ),
      Query(
          id=2,
          question="What was the weather like in Tokyo in 2021?",
          dependencies=[],
          tools=["get_weather_by_year"],
      ),
      Query(
          id=3,
          question="What was the weather like in Tokyo in 2022?",
          dependencies=[],
          tools=["get_weather_by_year"],
      ),
      Query(
          id=4,
          question="Compare the weather data for Tokyo from 2020 to 2022",
          dependencies=[1, 2, 3],
          tools=[],
      ),
  ]
"""
result = execute_query_plan(query_plan)
print(result)
# Output:
"""
Comparing the weather data for Tokyo from 2020 to 2022, we can observe the following trends:

1. Overall warming trend:
   - There's a general increase in temperatures across all months from 2020 to 2022.
   - The average annual temperature has risen each year.

2. Winter months (Dec-Feb):
   - 2020 had the coldest winters, with 2021 and 2022 progressively warmer.
   - January saw the most significant increase: 42°F (2020) to 48°F (2022).

3. Summer months (Jun-Aug):
   - Summer temperatures have increased each year.
   - August shows the most dramatic rise: 81°F (2020) to 87°F (2022).

4. Spring and Fall:
   - Both seasons show consistent warming trends.
   - March temperatures rose from 49°F (2020) to 56°F (2022).
   - October increased from 65°F (2020) to 71°F (2022).

5. Month with highest temperature:
   - In all three years, August was the hottest month.
   - The peak temperature increased from 81°F (2020) to 87°F (2022).

6. Month with lowest temperature:
   - January was consistently the coldest month.
   - The lowest temperature increased from 42°F (2020) to 48°F (2022).

In summary, Tokyo experienced a clear warming trend from 2020 to 2022, with temperatures increasing across all months, most notably in winter and summer periods.
"""
