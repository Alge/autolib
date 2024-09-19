import http.client
import json
import os
import logging
import textwrap
import subprocess
import sys
import importlib

logger = logging.getLogger("autolib")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s : %(name)s : %(message)s')

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
streamHandler.setLevel(logging.INFO)
logger.addHandler(streamHandler)

_aimethods = {}


usercontext = ""

def __getattr__(name):

    def installPipPackage(package_name):

        # Install he new package
        try:
            logger.info("Installing package from pip: %s", package_name)
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--break-system-packages"])
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while installing {package_name}: {str(e)}")
            raise e
        # Import it
        try:
            logger.info("Importing newly installed package: %s", package_name)
            return importlib.import_module(package_name)
        except ImportError as e:
            print(f"An error occurred while importing {package_name}: {str(e)}")
            raise e

    def generateContext():
        context = """Generate python3 code that implements this function.
Don't answer with anything but the python code.
All code must be included and be runnable, don't leave anything out
Implement all parts of the function

All imports needs to be done inside the function.

Do not include sample usage of the function.\n"""

        if len(_aimethods):
            context += "The following functions does already exist:\n"
            for methodname in _aimethods:
                context += f"autolib.{methodname}("
                for argtype in _aimethods[methodname]['args']:
                    context += f"{str(argtype)}, "
                for argname, argtype in _aimethods[methodname]['kwargs'].items():
                    context += f"{argname}:{str(argtype)}, "
                context += ")\n"
            context += "\n"

        #context += "You can assume that any methods you need already exists in the 'autolib' library as long as you give them descriptive names"
        context += "\n"

        context += usercontext

        logger.debug("Context:")
        logger.debug(context)

        return context


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
                    "content": generateContext()},
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
            args_list += f"{type(arg)}\n"

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

        # Store metadata about this method for later use in prompts
        args_list = []
        kwargs_dict = {}

        for arg in args:
            args_list.append(type(arg))
        for argname, value in kwargs.items():
            kwargs_dict[argname] = type(value)

        _aimethods[name] = {'text': response, 'args': args_list, 'kwargs': kwargs_dict}

        logger.debug("_aimethods representation")
        logger.debug(_aimethods[name])

        # This is very dangerous. Please don't use this outside a sandbox...
        exec(response)

        _aimethods[name]['function'] = locals()[name]

        globals()[name] = locals()[name]

        last_exception = None
        while 1: # Try a few times
            try:
                res = globals()[name](*args, **kwargs)
                return res

            except Exception as e:
                # Same exception as last time, no use trying again
                if e == last_exception:
                    raise e
                last_exception = e

                # Check if we are missing a module, maybe we can install it with pip?
                if isinstance(e, ModuleNotFoundError):
                    # Exctract the module name
                    start = str(e).index("'")
                    stop = str(e).index("'", start+1)
                    module_name = str(e)[start+1:stop]
                    logger.info("Missing module: %s", module_name)
                    installPipPackage(module_name)
                    continue

    return method




