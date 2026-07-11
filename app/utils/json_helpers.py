def clean_json_response(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No valid JSON found in Gemini response.")
    return text[start:end+1]