# Email Agent
I used OpenRouter, which provides a unified API for multiple AI Models. While
I have never used it before, I have heard good things. They provide a (beta)
Python SDK and my usage of it was simple enough that there were no issues despite
not yet having a stable version. Also, it has a generous free tier.

I decided that defining a tool for the model to use would be the way to go, since
it was mentioned that we should dynamically discover the schema. So, we want the model
to interface with the local DuckDB database using the existing python library already
defined in the pyproject.toml. The tool definition
exists in tools.py.

## Model Selection
I used GLM-4.5-air, since it was a highly rated within OpenRouter's free rankings,
and since it is open-source/open-weight. I also figured that tool support was necessary,
and it supports that.

## Future Work
OpenRouter's main value proposition is that it can access many models, so with more time
I would examine different models and compare the output between them.

## Example Output
!(./example-output.png)
