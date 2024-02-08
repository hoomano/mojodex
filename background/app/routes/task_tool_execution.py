from flask import request
from flask_restful import Resource
from app import db, executor
from db_models import *

from models.cortex.task_tool_execution_cortex import TaskToolExecutionCortex


class TaskToolExecution(Resource):
    def post(self):
        try:
            timestamp = request.json['datetime']
            task_tool_execution_pk = request.json['task_tool_execution_pk']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check follow_up exists
            task_tool_execution = db.session.query(MdTaskToolExecution).filter(
                MdTaskToolExecution.task_tool_execution_pk == task_tool_execution_pk).first()
            if task_tool_execution is None:
                return {"error": "task_tool_execution not found"}, 404

            task_tool_execution_cortex = TaskToolExecutionCortex(task_tool_execution)

            def run_task_tool_execution_cortex(cortex):
                try:
                    cortex.execute_task_tool()
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_task_tool_execution_cortex, task_tool_execution_cortex)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in task_tool_execution : {e}"}, 404
