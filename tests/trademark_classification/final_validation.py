import json


with open("./final_validated_keywords_per_classes.json", "r") as f:
    data = json.load(f) 
    # ={"class_number": [new_keyword1, new_keyword2, ...], ...}

# for each class, remove duplicated keywords
for class_number, keywords in data.items():
    data[class_number] = list(set(keywords))

data = dict(sorted(data.items()))
print(data)

