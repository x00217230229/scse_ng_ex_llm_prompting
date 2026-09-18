import json
import os
import ollama

def load_items(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]

def get_unclaimed_items(items):
    return [item for item in items if item["status"] == "unclaimed"]

def save_result(result, filename):
    dir_path = os.path.dirname(filename)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def build_prompt(description, available_items):
    items_json = json.dumps(available_items, ensure_ascii=False, indent=2)
    system_prompt = """
You are a campus lost-and-found matching assistant.
Rules:
1. Only use the provided JSON item list for matching.
2. Not all the details of an item must match to be a possible match.
3. Return ONLY JSON, no extra text.
4. Output structure exactly:
{
    "matches": ["ITEM_ID"],
    "confidence": "LOW"
}
5. matches: list of possible item IDs. Empty list if no matches.
6. confidence must be LOW / MEDIUM / HIGH.
"""
    user_prompt = f"""
User lost item description:
{description}

Available unclaimed found items:
{items_json}

Find all possible matches and output only JSON.
"""
    return system_prompt, user_prompt

def ask_qwen(system_prompt, user_prompt):
    response = ollama.chat(
        model="qwen",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response["message"]["content"]

def parse_response(response_text):
    return json.loads(response_text)

def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if "matches" not in result or "confidence" not in result:
        return False
    matches = result["matches"]
    confidence = result["confidence"]
    if not isinstance(matches, list) or not isinstance(confidence, str):
        return False
    if confidence not in ("LOW", "MEDIUM", "HIGH"):
        return False
    valid_ids = {i["id"] for i in available_items}
    for mid in matches:
        if mid not in valid_ids:
            return False
    return True

def display_matches(result, available_items, user_description):
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    print(f"Describe the item you lost: {user_description}")
    print("Searching for possible matches...")
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print("Possible matches:")
    item_map = {i["id"]:i for i in available_items}
    if not result["matches"]:
        print("No matches found. Matches = []")
    else:
        for mid in result["matches"]:
            it = item_map[mid]
            print(f"ID: {mid}")
            print(f"Item: {it['item']}")
            print(f"Color: {it['color']}")
            print(f"Location: {it['location']}")
            print(f"Date found: {it['date']}")
    save_result(result, "output/match_result.json")
    print("Result saved to output/match_result.json")

def main():
    all_items = load_items("found_items.json")
    unclaimed_items = get_unclaimed_items(all_items)
    user_desc = input("Please describe your lost item: ")
    sys_prompt, usr_prompt = build_prompt(user_desc, unclaimed_items)
    raw_response = ask_qwen(sys_prompt, usr_prompt)
    parsed_result = parse_response(raw_response)
    if not validate_result(parsed_result, unclaimed_items):
        print("Invalid result from model")
        return
    display_matches(parsed_result, unclaimed_items, user_desc)

if __name__ == "__main__":
    main()


