import http.client
import json
import os
import logging
import textwrap

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

        conn = http.client.HTTPSConnection("api.openai.com")
        endpoint = "/v1/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY")}'
        }

        data = {
            #'model':"gpt-3.5-turbo",
            'model':"gpt-4o-2024-08-06",
            'messages': [
                {
                    "role": "system",
                    "content": """Generate python3 code that implements this function.
Don't answer with anything but the python code.
Do not under any circumstances import modules from outside the python standard library
All code must be included and be runnable, don't leave anything out
Implement all parts of the function

All imports needs to be done inside the function
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        json_data = json.dumps(data)

        conn.request("POST", endpoint, body=json_data, headers=headers)

        response = conn.getresponse()

        response_data = json.load(response)

        logger.debug(response_data)

        return response_data['choices'][0]['message']['content']

    def generatePrompt(name, args, kwargs):

        args_list = "Positional arguments:\n"
        for arg in list(args):
            args_list += f"- {type(arg)}\n"

        kwargs_list = "Keyword arguments:\n"
        for kwname, arg in kwargs.items():
            args_list += f"{kwname} - {type(arg)}\n"

        prompt = f"""Generate a function with name '{name}' that takes in the following arguments:
{args_list}
{kwargs_list}"""

        return prompt

    # This method is called when trying to access a method that doesn't exist
    def method(*args, **kwargs):

        prompt = generatePrompt(name, args, kwargs)
        logger.debug(f"Generated prompt for method: {name}")
        logger.debug(prompt)

        response = generateCodeFromOpenAI(prompt).strip()

        logger.debug(f"Raw response\n{response}")

        # Remove first and last line when chatGTP returns what language it responds in
        if "python" in response.split("\n")[0]:
            response = "\n".join(response.split("\n")[1:])
            response = response.split('```')[0]
        response = textwrap.dedent(response)

        logger.info(f"Generated function:\n{response}")

        aimethods[name] = {'text': response}

        # This is very dangerous. Please don't use this outside a sandbox!!!!
        exec(response)

        aimethods[name]['function'] = locals()[name]

        globals()[name] = locals()[name]

        return globals()[name](*args, **kwargs)

    
    return method




