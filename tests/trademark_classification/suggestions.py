import json


with open("./suggestions.json", "r") as f:
    json_response = json.load(f)
suggestions = json_response['suggestions']

new_keywords_per_classes = {}
for suggestion in suggestions:
    #print(suggestion)
    suggested_terms = suggestion['suggestedTerms']
    for suggested_term in suggested_terms:
        class_ = suggested_term['classNumber']
        new_term = suggested_term['text']
        if class_ not in new_keywords_per_classes:
            new_keywords_per_classes[class_] = []
        new_keywords_per_classes[class_].append(new_term)

print(new_keywords_per_classes)