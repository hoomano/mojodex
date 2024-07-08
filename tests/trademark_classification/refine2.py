def _get_classification_dict_from_formatted_string(draft_classification: str):
        try:
            classes = draft_classification.split("\n\n")
            # create a list containing [{"class_number": X, 'keywords': [keyword1, keyword2, ...]}, ...]
            classes_list = []
            for class_ in classes:
                class_number, keywords = class_.split("\n", 1)
                # remove 'Class' from class_number
                class_number = class_number.lower().replace("class", "").strip()
                # if keywords ends with ".", remove it
                if keywords.endswith("."):
                    keywords = keywords[:-1]
                classes_list.append({"class_number": int(class_number), 'keywords': keywords.split("; ")})
            return classes_list
        except Exception as e:
            raise Exception(f" _construct_classification_dict :: {e}")

with open('./refine_trademark_classification_response.txt', 'r') as f:
    response = f.read()

# get dict from response
refined_classification = _get_classification_dict_from_formatted_string(response)
print(refined_classification)

# check every keyword outputed by gpt existed in original classes_dict, else remove it
refined_classification_dict = {}
for classification in refined_classification:
    class_number = classification['class_number']
    keywords = classification['keywords']
    #print(refined_classification[class_number])
    #refined_classification[class_number] = [keyword for keyword in keywords if keyword in classes_dict[class_number]]
