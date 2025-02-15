# Evaluating Documentation Agent

In this recipe, we will be using taking our [Documentation Agent](https://github.com/Mirascope/mirascope/tree/dev/examples/cookbook/agents/documentation_agent/agent.py) example and running evaluations on the LLM call. We will be exploring various different evaluations we can run to ensure quality and expected behavior.

??? tip "Mirascope Concepts Used"

    - [Prompts](../../learn/prompts.md)
    - [Calls](../../learn/calls.md)
    - [Chaining](../../learn/chaining.md)
    - [Evals](../../learn/evals.md)

??? note "Check out the Documentation Agent Cookbook"

    We will be using our `DocumentationAgent` for our evaluations. For a detailed explanation regarding this code snippet, refer to the [Documentation Agent Cookbook](../agents/documentation_agent.md).


## Basic Evaluations

We will first test the functionality of our LLM Rerank function to ensure it performs as intended. We have prepared a list of mock documents, each with an assigned semantic score, simulating retrieval from our vector store. The LLM Rerank function will then reorder these documents based on their relevance to the query, rather than relying solely on their semantic scores.

```python

--8<-- "examples/cookbook/agents/documentation_agent/documents.py:2:5"
documents = [

]
@pytest.mark.parametrize(
    
    "query,documents,top_n_ids",
    ("What is Bob's favorite food", documents, {3, 0}),
)
--8<-- "examples/cookbook/agents/documentation_agent/test_agent.py:119:124"
```

Our tests:

* Ensures that all returned documents have a relevancy score above 5 out of 10, indicating a minimum threshold of relevance.
* Checks that the top-ranked documents (as many as specified in `top_n_ids`) are within the set of expected documents, allowing for some flexibility in the exact ordering.

The test accommodates the non-deterministic nature of LLM-based reranking. While we can't expect identical results in every run, especially when multiple documents are similarly relevant, we can at least verify that the output falls within our boundaries.

## Evaluating Code Snippets and General Q&A

The example documents we are using for our `DocumentationAgent` are the Mirascope docs. Since Mirascope is a python library, users are likely to ask about both code implementation and conceptual understanding. Therefore, our evaluation process needs to address these two distinct scenarios.

### Evaluating Code Snippet

To ensure the accuracy and functionality of the LLM-generated code, we implement a two-step verification process:

* Syntax Validation: We create a general Python code tester to verify the syntactic correctness of the generated code.
* Import Verification: Since syntax validation alone is insufficient, we incorporate an additional check for proper imports. This step confirms all modules and dependencies are valid and no "magic" imports exist.

```python
--8<-- "examples/cookbook/agents/documentation_agent/test_agent.py:1:3"
--8<-- "examples/cookbook/agents/documentation_agent/test_agent.py:18:92"
```

Now that we have our `check_syntax` and `is_importable` tests working, we can test our LLM output:

```python
--8<-- "examples/cookbook/agents/documentation_agent/test_agent.py:127:140"
```

### Evaluating General Q&A

For non-code responses generated by the LLM, our primary goal is to verify that the LLM is sourcing its responses directly from the Mirascope documentation rather than relying on its broader knowledge base. Here we require that the LLM's response contains a sentence verbatim.

```python
@pytest.mark.parametrize(
    "query,expected",
    [
        ("What is Mirascope?", "a toolkit for building AI-powered applications"),
    ],
)
def test_documentation_agent(query: str, expected: str):
    documentation_agent = DocumentationAgent()
    response = documentation_agent._call(query)
    if response.classification == "general":
        assert expected in response.content
```

When adapting this recipe to your specific use-case, consider the following:

* Update the Few-Shot examples to match your documents.
* Experiment with other providers for LLM Reranking or use multiple LLM Rerankers and average out the scores.
* Add history to the `DocumentationAgent` and have the LLM generate the query for `get_documents` for a more relevant semantic search.
