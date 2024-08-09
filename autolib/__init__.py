# world.py
from openai import OpenAI
import os

import logging

logger = logging.getLogger("autolib")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s : %(name)s : %(message)s')

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
streamHandler.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)

aimethods = {}


def __getattr__(name):
    def generateCodeFromOpenAI(prompt):
        
        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        logger.debug(f"Fetching results for prompt: {prompt}")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate python3 code that implements this function. Don't answer with anything but the python code. Feel free to import things from the python standard libraries inside this function if needed"},
                {"role": "user", "content": prompt}
            ]
        )
        logger.debug("Got response")
        logger.debug(response.choices[0].message.content)
        return response.choices[0].message.content

    def generatePrompt(name, args, kwargs):

        args_list = "Positional arguments:\n"
        for arg in list(args):
            args_list += f"- {type(arg)}\n"

        kwargs_list = "Keyword arguments:\n"
        for name, arg in kwargs:
            args_list += f"{name} - {type(arg)}\n"

        prompt = f"""Generate a function with name '{name}' that takes in the following arguments:
{args_list}
{kwargs_list}"""

        return prompt

    # This method is called when trying to access a method that doesn't exist
    def method(*args, **kwargs):
        logger.debug(f"Method '{name}' called with args: {args} and kwargs: {kwargs}")
        prompt = generatePrompt(name, args, kwargs)
        logger.debug("Generated prompt")
        logger.debug(prompt)

        response = generateCodeFromOpenAI(prompt)

        # Remove first and last line
        response = "\n".join(response.split("\n")[1:-1])

        aimethods[name] = {'text': response}

        logger.debug(f"aimethods: {aimethods}")

        # This is very dangerous. Please don't use this outside a sandbox!!!!
        exec(response)

        aimethods[name]['function'] = locals['name']

        logger.debug("Adding the function to globals")

        globals()[name] = locals()[name]

        return globals()[name](*args, **kwargs)

    
    return method




