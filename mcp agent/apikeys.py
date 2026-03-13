import google.generativeai as genai

genai.configure(api_key="AIzaSyDhkZQZukaAmQbf599UkiRfMUqhMZdmEqs")

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)