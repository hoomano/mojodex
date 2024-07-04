from mojodex_core.user_storage_manager.user_images_file_manager import UserImagesFileManager


class UserTaskExecutionInputsManager:

    drop_down_type = "drop_down_list"
    image_type = "image"
    multiple_images_type = "multiple_images"

    def construct_inputs_from_request(self, user_task_execution_json_input_values, inputs, files, user_id, session_id):
        try:
            # ensure inputs is a list of dicts and each dict has the required fields (input_name and input_value)
            if not isinstance(inputs, list):
                return {"error": "inputs must be a list"}, 400
           
            for filled_input in inputs:
                # check format
                if not isinstance(filled_input, dict):
                    raise KeyError("inputs must be a list of dicts")
                if "input_name" not in filled_input or "input_value" not in filled_input:
                    raise KeyError("inputs must be a list of dicts with keys input_name and input_value")
                # look for corresponding input in json_input_values
                for input in user_task_execution_json_input_values:
                    if input["input_name"] == filled_input["input_name"]:
                        if input["type"] == self.drop_down_type:
                            possible_values = [value["value"] for value in input["possible_values"]]
                            if filled_input["input_value"] not in possible_values:
                                return {"error": f"Invalid value for input {input['input_name']}"}, 400
                        input["value"] = filled_input["input_value"]
                    elif "_".join(filled_input["input_name"].split("_")[:-1]) == input["input_name"]:
                        if input["type"] == self.multiple_images_type:
                            if input["value"] is None:
                                input["value"] = [filled_input["input_value"]]
                            else:
                                input["value"].append(filled_input["input_value"])

            for image_input in files:
                # look for corresponding input in json_input_values
                for input in user_task_execution_json_input_values:
                    if input["type"] == self.image_type:
                        if input["input_name"] == image_input:
                            filename = input["value"]
                            UserImagesFileManager().store_image_file(files[image_input], filename, user_id, session_id)
                    if input["type"] == self.multiple_images_type:
                        image_name = "_".join(image_input.split("_")[:-1])
                        image_index = int(image_input.split("_")[-1])
                        if input["input_name"] == image_name:
                            filename = input["value"][image_index]
                            UserImagesFileManager().store_image_file(files[image_input], filename, user_id, session_id)

            return user_task_execution_json_input_values
        except Exception as e:
            raise Exception(f"UserTaskExecutionInputsManager - construct_inputs_from_request: {e}")
