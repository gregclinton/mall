from fastapi import FastAPI, Request
import llm
from tool import bench
from time import sleep

threads = {}
max_llm_invokes = 10

def post_off_server(url, prompt):
    # here we would connect with another chatbot
    # set up a thread
    # and chat until we got some answer
    return { "content": "Sorry, can't help you. "}

def invoke(thread, prompt):
    message = lambda role, content: { "role": role, "content": content }
    how = [message("system", "\n\n".join(open(f"how/{f}").read() for f in ["plot"]))]
    bulk = None

    messages = threads.setdefault(thread, [])
    messages.append(message("user", prompt))
    content = None

    while not content:
        sleep(0.2) # in case this loop runs away
        response = llm.invoke(how + messages)
        content = response.get("content")

        if llm.counter > max_llm_invokes:
            content = "Could you please rephrase that?"
        elif "url" in response:
            response = post_off_server(response["url"], response["prompt"])
            content = response.get("content")
        elif "tool" in response:
            tool = response["tool"]
            if tool in bench:
                try:
                    output = bench[tool](response["text"])
                    if len(output) > 20000:
                        bulk = output
                        output = "success"
                    messages.append(message("user", output))
                except Exception as e:
                    content = str(e)
            else:
                content = response["tool"] + " tool does not exist."

    messages.append(message("assistant", content))
    return { "content": bulk or content }

app = FastAPI()

@app.post('/mall/messages/{thread}')
async def post_message(req: Request, thread: str):
    llm.reset_counter()
    return invoke(thread, (await req.json())['prompt'])

# print(invoke("123456", "Plot exponential from -3 to 3.")["content"])
