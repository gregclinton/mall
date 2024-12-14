# https://platform.openai.com/docs/api-reference/chat

import requests
import os
import json
import tool

def reset(thread):
    return tool.reset(thread)

def invoke(messages, thread):
    content = None
    count = 0
    bench = tool.open()
    tool_messages = []

    while not content and count < 10:
        count += 1
        message = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers = {
                'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
                'Content-Type': 'application/json',
            },
            json = {
                "model": thread["model"],
                "temperature": thread["temperature"],
                "messages": messages + tool_messages,
                "tools": bench,
                "tool_choice": "auto"
            }).json()["choices"][0]["message"]

        content = message.get("content")

        if not content:
            tool_messages.append(message)

            for call in message.get("tool_calls", []):
                try:
                    fn = call["function"]
                    name = fn["name"]
                    args = json.loads(fn["arguments"])
                    args["thread"] = thread
                    output = tool.run(name, args)
                    print(f"{name}:")

                    if name in ['json']:
                        content = output
                        break
                    else:
                        del args["thread"]

                        [print(arg) for arg in args.values()]
                        print(f"\n{output}\n")

                        if name == "recap":
                            messages.clear()

                        tool_messages.append({
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "name": name,
                            "content": output
                        })

                except Exception as e:
                    return str(e)

    tool.close()
    return content or "Could you rephrase that, please?"
