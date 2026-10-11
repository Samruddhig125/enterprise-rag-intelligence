import os
from dotenv import load_dotenv, find_dotenv

path = find_dotenv(usecwd=True)
print(".env found at:", path or "NOT FOUND")
load_dotenv(path)

key = os.getenv("GROQ_API_KEY")
print("GROQ_API_KEY loaded:", bool(key))

from groq import Groq
for m in sorted(x.id for x in Groq(api_key=key).models.list().data):
    print(m)