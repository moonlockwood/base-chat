import datetime
import openai
import asyncio
import jinja2

import MessageManager

class BaseModelChat:
    def __init__(self):
        self.init_hyperbolic()
        self.initMessages()
      
    def init_hyperbolic(self):
        filename = "settings/hyperbolic_key.txt"
        with open(filename, "r") as f:
            HYPERBOLIC_API_KEY = f.read()        
        self.client = openai.OpenAI(
            api_key=HYPERBOLIC_API_KEY,
            base_url="https://api.hyperbolic.xyz/v1",
            )
        self.model = "meta-llama/Meta-Llama-3.1-405B-FP8"

    def initMessages(self):
        self.chat_template = """{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"""
        self.messages = MessageManager.Messages()

    def format_chat(self, messages, add_generation_prompt=False):
        template = jinja2.Template(self.chat_template)
        formatted = template.render(messages=messages, add_generation_prompt=add_generation_prompt)
        return formatted

    async def chat_with_server(self, prompt):

        context_setting = "Respond however you want."

        full_prompt = f"{context_setting}\n\n{prompt}"
        self.messages.add_message("user", full_prompt)
        initial_prompt = "<|startoftext|>" + full_prompt 
        chat_history = self.messages.messages
        formatted_input = self.format_chat(chat_history, add_generation_prompt=True)
        full_prompt = initial_prompt + "\n" + formatted_input
        self.complete_response = ""

        async def fetch():
            try:
                response = self.client.completions.create(
                    model=self.model,
                    prompt=full_prompt,
                    temperature=1.0,
                    max_tokens=1024,
                    stream=True,
                    stop=['<|im_end|>']
                )    
                for chunk in response:
                    content = chunk.choices[0].text
                    if content:
                        self.complete_response += content
                        yield content

                self.messages.add_message("assistant", self.complete_response)
                print()  # For new line after the response
            
            except Exception as e:
                print(f"An error occurred: {e}")

        async for chunk in fetch():
            await self.print_chunk(chunk)
        print()

    async def print_chunk(self, chunk):
        for char in chunk:
            print(char, end='', flush=True)
            await asyncio.sleep(0.02)

    async def chat(self):
        print("\033[2J\033[H")  # Clear the screen
        timestamp = str(datetime.datetime.now().strftime("%H:%M:%S - %m-%d-%y"))
        print(f"{timestamp}\n")
        print("     /--------============--------\ ")
        print("     --------: Base Model :-------- ")
        print("     \--------============--------/ ")

        while True:
            print('\n---------')
            prompt = await asyncio.get_event_loop().run_in_executor(None, input, "◊> ")
            print('---------\n')
            if prompt.lower() in ["/exit", "/quit"]:
                break
            elif prompt == "/save":
                filename = f"Conversation - {timestamp}.txt"
                self.messages.save_conversation(filename)
                print(f"\r\r\rConversation saved to '{filename}'")
            elif prompt.startswith("/count"):
                count = len(self.messages.messages)
                print(f"Total messages: {count}")
            else:
                await self.chat_with_server(prompt)
          
async def main():
    obj = BaseModelChat()
    await obj.chat()

if __name__ == "__main__":
    asyncio.run(main())



'''
<|startoftext|>
You are a helpful AI assistant
<|im_start|>user
Hello<|im_end|>
<|im_start|>assistant
Hi there!<|im_end|>
<|im_start|>assistant
'''
